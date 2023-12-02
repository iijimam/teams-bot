# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from datetime import datetime
from aiohttp.helpers import NO_EXTENSIONS

from recognizers_number import recognize_number, Culture
from recognizers_date_time import recognize_datetime

from botbuilder.core import (
    ActivityHandler,
    ConversationState,
    TurnContext,
    UserState,
    MessageFactory,
    CardFactory
)
from botbuilder.schema import Activity

#from data_models import ConversationFlow, Question, UserProfile
from data_models import ConversationFlow, Question, ObservationProfile

import os
import json
import bots.GoIRIS as GoIRIS


class ValidationResult:
    def __init__(
        self, is_valid: bool = False, value: object = None, message: str = None
    ):
        self.is_valid = is_valid
        self.value = value
        self.message = message


class CustomPromptBot(ActivityHandler):
    def __init__(self, conversation_state: ConversationState, user_state: UserState):
        if conversation_state is None:
            raise TypeError(
                "[CustomPromptBot]: Missing parameter. conversation_state is required but None was given"
            )
        if user_state is None:
            raise TypeError(
                "[CustomPromptBot]: Missing parameter. user_state is required but None was given"
            )

        self.conversation_state = conversation_state
        self.user_state = user_state

        self.flow_accessor = self.conversation_state.create_property("ConversationFlow")
        #self.profile_accessor = self.user_state.create_property("UserProfile")
        self.profile_accessor = self.user_state.create_property("ObservationProfile")

    async def on_message_activity(self, turn_context: TurnContext):
        # Get the state properties from the turn context.
        #profile = await self.profile_accessor.get(turn_context, UserProfile)
        profile = await self.profile_accessor.get(turn_context, ObservationProfile)
        flow = await self.flow_accessor.get(turn_context, ConversationFlow)

        if flow.last_question_asked == Question.YN1:
            yn=turn_context.activity.value

            if yn["answer"]=="no":
                flow.last_question_asked=Question.NONE
                await turn_context.send_activity(
                    MessageFactory.text("Okay. I won't do anything now.")
                )
                return

            else :
                #IRIS呼出
                flow.last_question_asked=Question.O2
                returnFromIRIS=GoIRIS.get_iris(profile.MRN)
                if returnFromIRIS["Status"]=="OK":                  
                    profile.PatientName=returnFromIRIS["PatientName"]
                    profile.PatientResourceID=returnFromIRIS["PatientResourceID"]
                    await turn_context.send_activity(
                        MessageFactory.text(f"The number you entered：**{profile.MRN}**. Patient name is **{profile.PatientName}**. The resource id is **{profile.PatientResourceID}**.")
                    )
                else:
                    await turn_context.send_activity(
                        MessageFactory.text(f"Retreieval failure：{returnFromIRIS['Message']}")
                    )
                    return

        if flow.last_question_asked == Question.YN2:
            yn=turn_context.activity.value
            flow.last_question_asked=Question.NONE

            if yn["answer"]=="no":
                await turn_context.send_activity(
                    MessageFactory.text("Okay. I won't do anything now.")
                )
                return
            
            else :
                #IRIS呼出
                #postdata={"Name":profile.Name, "EMPID":profile,"Location":profile.Location}
                #returnFromIRIS=GoIRIS.post_iris(postdata)
                print(profile.MRN)
                returnFromIRIS=GoIRIS.post_iris(profile.to_json())
                #retjson=json.dumps(returnFromIRIS, ensure_ascii=False)
                if returnFromIRIS["Status"]=="OK":                    
                    await turn_context.send_activity(
                        MessageFactory.text(f"**{profile.MRN}**：**{profile.PatientName}** 's value of pulse oximeter is **{profile.O2}**. I have registerd the value to FHIR repogitory. The resource id of the patient is **{profile.PatientResourceID}**.")
                    )
                else:
                    await turn_context.send_activity(
                        MessageFactory.text(f"Failed to save.：{returnFromIRIS['Message']}")
                    )
            return

        await self._fill_out_user_profile(flow, profile, turn_context)

        # Save changes to UserState and ConversationState
        await self.conversation_state.save_changes(turn_context)
        await self.user_state.save_changes(turn_context)


    async def _fill_out_user_profile(
        #self, flow: ConversationFlow, profile: UserProfile, turn_context: TurnContext
        self, flow: ConversationFlow, profile: ObservationProfile, turn_context: TurnContext
    ):
        #user_input = turn_context.activity.text.strip()
        if not turn_context.activity.text==None:
            user_input=turn_context.activity.text.strip() 

        # ask for 患者番号
        if flow.last_question_asked == Question.NONE:
            await turn_context.send_activity(
                MessageFactory.text("Let's get started! Please input patient number.")
            )
            flow.last_question_asked = Question.MRN

        # 患者検索実行
        elif flow.last_question_asked == Question.MRN:
            validate_result = self._validate_name(user_input)
            if not validate_result.is_valid:
                await turn_context.send_activity(
                    MessageFactory.text(validate_result.message)
                )
            else:
                profile.MRN = validate_result.value
                await turn_context.send_activity(
                    MessageFactory.text(f"Your input numer is **{profile.MRN}**. I'll start search.")
                )

                card_path = os.path.join(os.getcwd(), "bots/YesNoCard1.json")
                with open(card_path, "rb") as in_file:
                    template_json = json.load(in_file)
                
                adaptive_card_attachment = Activity(
                    attachments=[CardFactory.adaptive_card(template_json)]
                )

                await turn_context.send_activity(adaptive_card_attachment)
            
            flow.last_question_asked = Question.YN1

        #パルスオキシメータ入力
        elif flow.last_question_asked == Question.O2:
            await turn_context.send_activity(
                MessageFactory.text("Please enter pulse oximeter measurement results.")
            )
            flow.last_question_asked = Question.O2Conf
        #
        elif flow.last_question_asked == Question.O2Conf:
            validate_result = self._validate_string(user_input)
            if not validate_result.is_valid:
                await turn_context.send_activity(
                    MessageFactory.text(validate_result.message)
                )
            else:
                profile.O2 = validate_result.value                 
                await turn_context.send_activity(
                    MessageFactory.text(f"Pulse oximeter values entered by you：**{profile.O2}**.")
                )
                card_path = os.path.join(os.getcwd(), "bots/YesNoCard2.json")
                with open(card_path, "rb") as in_file:
                    template_json = json.load(in_file)
                
                adaptive_card_attachment = Activity(
                    attachments=[CardFactory.adaptive_card(template_json)]
                )
                await turn_context.send_activity(adaptive_card_attachment)

            flow.last_question_asked = Question.YN2


    def _validate_name(self, user_input: str) -> ValidationResult:
        if not user_input:
            return ValidationResult(
                is_valid=False,
                message="Please enter a name that contains at least one character.",
            )

        return ValidationResult(is_valid=True, value=user_input)

    def _validate_string(self, user_input: str) -> ValidationResult:
        if not user_input:
            return ValidationResult(
                is_valid=False,
                message="文字列を入力してください",
            )

        return ValidationResult(is_valid=True, value=user_input)

    def _validate_age(self, user_input: str) -> ValidationResult:
        # Attempt to convert the Recognizer result to an integer. This works for "a dozen", "twelve", "12", and so on.
        # The recognizer returns a list of potential recognition results, if any.
        results = recognize_number(user_input, Culture.English)
        for result in results:
            if "value" in result.resolution:
                age = int(result.resolution["value"])
                if 18 <= age <= 120:
                    return ValidationResult(is_valid=True, value=age)

        return ValidationResult(
            is_valid=False, message="Please enter an age between 18 and 120."
        )

    def _validate_date(self, user_input: str) -> ValidationResult:
        try:
            # Try to recognize the input as a date-time. This works for responses such as "11/14/2018", "9pm",
            # "tomorrow", "Sunday at 5pm", and so on. The recognizer returns a list of potential recognition results,
            # if any.
            results = recognize_datetime(user_input, Culture.English)
            for result in results:
                for resolution in result.resolution["values"]:
                    if "value" in resolution:
                        now = datetime.now()

                        value = resolution["value"]
                        if resolution["type"] == "date":
                            candidate = datetime.strptime(value, "%Y-%m-%d")
                        elif resolution["type"] == "time":
                            candidate = datetime.strptime(value, "%H:%M:%S")
                            candidate = candidate.replace(
                                year=now.year, month=now.month, day=now.day
                            )
                        else:
                            candidate = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")

                        # user response must be more than an hour out
                        diff = candidate - now
                        if diff.total_seconds() >= 3600:
                            return ValidationResult(
                                is_valid=True,
                                value=candidate.strftime("%m/%d/%y"),
                            )

            return ValidationResult(
                is_valid=False,
                message="I'm sorry, please enter a date at least an hour out.",
            )
        except ValueError:
            return ValidationResult(
                is_valid=False,
                message="I'm sorry, I could not interpret that as an appropriate "
                "date. Please enter a date at least an hour out.",
            )


