import json
from typing import List


class DataClassBasic:
    def toJSON(self):
        return json.dumps(
            self,
            default=lambda o: o.__dict__,
            sort_keys=True,
            indent=4)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

class DataFromDict(DataClassBasic):
    def __init__(self, **entries):
        self.__dict__.update(entries)

    def toJSON(self):
        return json.dumps(
            self,
            default=lambda o: o.__dict__,
            sort_keys=True,
            indent=4)

class FlatSchedule(DataClassBasic):
    def __init__(self,
                 BaseParameters: 'FlatScheduleParameters' = None,
                 BaseSchedules: 'FlatScheduleBase' = None,
                 CurrentSchedules: 'FlatScheduleDetailed' = None):
        self.BaseParameters = BaseParameters if BaseParameters is not None else FlatScheduleParameters()
        self.BaseSchedules = BaseSchedules if BaseSchedules is not None else FlatScheduleBase()
        self.CurrentSchedules = CurrentSchedules if CurrentSchedules is not None else FlatScheduleDetailed()

class FlatScheduleDetailed(DataClassBasic):
    def __init__(self,
                 scheduleDay: List['Data_IntArray'] = None,
                 scheduleGroup: List['Data_IntArray'] = None,
                 scheduleLesson: List['Data_IntIntIntArrayArray'] = None,
                 cabinetLesson: List['Data_IntIntIntArrayArray'] = None,
                 teacherLesson: List['Data_IntIntIntArrayArray'] = None,
                 version: int = None):
        self.scheduleDay = scheduleDay if scheduleDay is not None else []
        self.scheduleGroup = scheduleGroup if scheduleGroup is not None else []
        self.scheduleLesson = scheduleLesson if scheduleLesson is not None else []
        self.cabinetLesson = cabinetLesson if cabinetLesson is not None else []
        self.teacherLesson = teacherLesson if teacherLesson is not None else []
        self.version = version

class FlatScheduleBase(DataClassBasic):
    def __init__(self,
                 nameList: List['Data_IntString'] = None,
                 scheduleName: List['Data_IntArray'] = None,
                 scheduleDay: List['Data_IntArray'] = None,
                 scheduleGroup: List['Data_IntArray'] = None,
                 scheduleLesson: List['Data_IntIntIntArrayArray'] = None,
                 cabinetLesson: List['Data_IntIntIntArrayArray'] = None,
                 teacherLesson: List['Data_IntIntIntArrayArray'] = None):
        self.nameList = nameList if nameList is not None else []
        self.scheduleName = scheduleName if scheduleName is not None else []
        self.scheduleDay = scheduleDay if scheduleDay is not None else []
        self.scheduleGroup = scheduleGroup if scheduleGroup is not None else []
        self.scheduleLesson = scheduleLesson if scheduleLesson is not None else []
        self.cabinetLesson = cabinetLesson if cabinetLesson is not None else []
        self.teacherLesson = teacherLesson if teacherLesson is not None else []

class FlatScheduleParameters(DataClassBasic):
    def __init__(self,
                 cabinetList: List['Data_IntString'] = None,
                 groupList: List['Data_IntString'] = None,
                 lessonList: List['Data_IntString'] = None,
                 teacherList: List['Data_IntString'] = None,
                 dayList: List['Data_IntDate'] = None):
        self.cabinetList = cabinetList if cabinetList is not None else []
        self.groupList = groupList if groupList is not None else []
        self.lessonList = lessonList if lessonList is not None else []
        self.teacherList = teacherList if teacherList is not None else []
        self.dayList = dayList if dayList is not None else []

class FlatScheduleResponse(DataClassBasic):
    def __init__(self,
                 scheduleCurrent: FlatScheduleDetailed | FlatScheduleBase = None,
                 scheduleStaged: FlatScheduleDetailed | FlatScheduleBase = None,
                 comparisonGeneral: bool = None,
                 comparisonSpecific: bool = None):
        self.scheduleCurrent = scheduleCurrent
        self.scheduleStaged = scheduleStaged
        self.comparisonGeneral = comparisonGeneral
        self.comparisonSpecific = comparisonSpecific


class Data_IntString(DataClassBasic):
    def __init__(self, id: int = None, title: str = None):
        self.id = id
        self.title = title

class Data_IntDate(DataClassBasic):
    def __init__(self, id: int = None, date: 'Date' = None):
        self.id = id
        self.date = date if date is not None else Date()

class Data_IntArray(DataClassBasic):
    def __init__(self, specialId: int = None, scheduleId: List[int] = None):
        self.specialId = specialId
        self.scheduleId = scheduleId if scheduleId is not None else []

class Data_IntIntIntArrayArray(DataClassBasic):
    def __init__(self,
                 scheduleId: int = None,
                 pairNum: int = None,
                 subPairs: List[int] = None,
                 subGroups: List[int] = None,
                 specialId: int = None):
        self.scheduleId = scheduleId
        self.pairNum = pairNum
        self.subPairs = subPairs if subPairs is not None else []
        self.subGroups = subGroups if subGroups is not None else []
        self.specialId = specialId


class Date(DataClassBasic):
    def __init__(self, year: int = None, month: int = None, day: int = None):
        self.year = year
        self.month = month
        self.day = day

class ScheduleDetailed(DataClassBasic):
    def __init__(self,
                 lessonNum: int = None,
                 discipline1: str = "-",
                 cabinet1: str = "-",
                 teacher1: str = "-",
                 discipline2: str = "-",
                 cabinet2: str = "-",
                 teacher2: str = "-",
                 discipline3: str = "-",
                 cabinet3: str = "-",
                 teacher3: str = "-"):
        self.lessonNum = lessonNum
        self.discipline1 = discipline1
        self.cabinet1 = cabinet1
        self.teacher1 = teacher1
        self.discipline2 = discipline2
        self.cabinet2 = cabinet2
        self.teacher2 = teacher2
        self.discipline3 = discipline3
        self.cabinet3 = cabinet3
        self.teacher3 = teacher3