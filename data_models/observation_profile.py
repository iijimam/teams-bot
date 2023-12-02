# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import json

class ObservationProfile:
    def __init__(self, mrn: str=None, pid: str = None, pname: str = None, o2: str = None):
        self.MRN=mrn
        self.PatientResourceID = pid
        self.PatientName =pname 
        self.O2 = o2

    def to_json(self):
        return json.dumps(self.__dict__, ensure_ascii=False).encode("utf-8")
