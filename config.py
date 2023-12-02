#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os

""" Bot Configuration """


class DefaultConfig:
    """ Bot Configuration """

    PORT = 3978
    APP_ID = os.environ.get("MicrosoftAppId", "80c19888-4244-4ec4-956e-b86a78c35907")
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "KMH8Q~Z2UMlxG8zMrMXtCpANg_yFoF3jgB-NbaWr")
    #APP_ID = os.environ.get("MicrosoftAppId", "")
    #APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")
