import copy
import datetime
import json
from typing import List, Optional

from rest_framework.utils.serializer_helpers import ReturnDict

from api.constants import MOBILE_APP_PAGE_COUNT, APP_TYPEID_PARAMETERS_DISCIPLINE, \
    APP_TYPEID_PARAMETERS_GROUP, APP_TYPEID_PARAMETERS_TEACHER, APP_TYPEID_PARAMETERS_CABINET, \
    APP_TYPEID_PARAMETERS_DATE, APP_TYPEID_IDENTIFIER_LIST
from api.data import Data_IntString, Data_IntDate, Date, FlatSchedule, FlatScheduleDetailed, FlatScheduleBase, \
    FlatScheduleParameters, Data_IntArray, ScheduleDetailed, Data_IntIntIntArrayArray, DataFromDict
from api.models import Model_FlatSchedule


# =================================================================================================================
# Basic utility stuff
# =================================================================================================================

def getById(id: int, array): # Data_IntString, Data_IntDate
    for item in array:
        if item.id == id:
            return item
    return None

def getById_Array(id: int, array): # Data_IntArray, Data_IntIntIntArrayArray
    for item in array:
        if item.specialId == id:
            return item
    return None

def getItemId_Date(dayList: List[Data_IntDate], date: Date) -> Optional[int]:
    for item in dayList:
        if date == item.date:
            return item.id
    return None

def getItemId_Title(itemList: List[Data_IntString], itemName: str) -> Optional[int]:
    if itemName is None:
        return None
    for item in itemList:
        if itemName == item.title:
            return item.id
    raise AssertionError(f"No item ID was found, some part of the DB is probably missing or incorrect ({itemName}).")

def getEmptyId(currentIds: List[int]) -> int:
    currentIds.sort()

    new_id = 0
    for e in currentIds:
        if new_id == e:
            new_id += 1
    return new_id

def getPossibleId_String(originalList: List[Data_IntString]) -> int:
    currentIds = []
    for item in originalList:
        currentIds.append(item.id)
    return getEmptyId(currentIds)

def getPossibleId_Date(originalList: List[Data_IntDate]) -> int:
    currentIds = []
    for item in originalList:
        currentIds.append(item.id)
    return getEmptyId(currentIds)

def getDataFromDictGeneric_HandleList(itemList: list):
    for i in range(len(itemList)):
        if isinstance(itemList[i], list):
            getDataFromDictGeneric_HandleList(itemList[i])
        if isinstance(itemList[i], dict):
            itemList[i] = getDataFromDictGeneric(itemList[i], False)
        elif not isinstance(itemList[i], (bool, int, float, str, DataFromDict)):
            raise TypeError(f"Got a variable type that is unaccounted for (getDataFromDictGeneric): {type(itemList[i])}.")
def getDataFromDictGeneric(dictionary: dict, first: bool = True):
    if first:
        dictionary = copy.deepcopy(dictionary)

    for key in dictionary.keys():
        value = dictionary.get(key)
        if isinstance(value, dict):
            dictionary[key] = getDataFromDictGeneric(value, False)
        elif isinstance(value, list):
            getDataFromDictGeneric_HandleList(value)
        elif isinstance(value, datetime.date):
            dictionary[key] = Date(value.year, value.month, value.day)
        elif not isinstance(value, (bool, int, float, str, DataFromDict)):
            raise TypeError(f"Got a variable type that is unaccounted for (getDataFromDictGeneric): {type(value)}.")
    return DataFromDict(**dictionary)

def getSavedSchedule() -> Model_FlatSchedule:
    return Model_FlatSchedule.objects.all()[0]

def getDayListData() -> List[Data_IntDate]:
    schedule = getSavedSchedule()
    dayList = copy.copy(schedule.BaseParameters[0][getParametersIdentifier(APP_TYPEID_PARAMETERS_DATE)])
    for i in range(len(dayList)):
        actualDate = datetime.datetime.strptime(str(dayList[i]['date']), "%Y-%m-%d").date()
        dayList[i] = Data_IntDate(dayList[i]['id'], Date(year=actualDate.year, month=actualDate.month, day=actualDate.day))
    return dayList

def getParametersIdentifier(id: int, daysAllowed: bool = True) -> str:
    id = int(id)
    if id == APP_TYPEID_PARAMETERS_DATE:
        if not daysAllowed:
            raise ValueError(f"Date TypeID was supplied when not allowed (uploadScheduleParameters).")

    identifier = getById(id, APP_TYPEID_IDENTIFIER_LIST)
    if identifier == None:
        raise ValueError(f"Incorrect TypeID was supplied (uploadScheduleParameters): {id}.")

    return identifier.title

def collectAllCurrentScheduleIds() -> list[int]:
    schedule_ids = []
    schedules = (getDataFromDictGeneric(getSavedSchedule().CurrentSchedules[0]), getDataFromDictGeneric(getSavedSchedule().CurrentSchedules[1]))
    for schedule in schedules:
        for item in schedule.scheduleDay:
            for id in item.scheduleId:
                if id not in schedule_ids:
                    schedule_ids.append(id)
        for item in schedule.scheduleGroup:
            for id in item.scheduleId:
                if id not in schedule_ids:
                    schedule_ids.append(id)
    return schedule_ids

def collectAllBaseScheduleIds() -> list[int]:
    schedule_ids = []
    schedules = (getDataFromDictGeneric(getSavedSchedule().BaseSchedules[0]), getDataFromDictGeneric(getSavedSchedule().BaseSchedules[1]))
    for schedule in schedules:
        for item in schedule.scheduleDay:
            for id in item.scheduleId:
                if id not in schedule_ids:
                    schedule_ids.append(id)
        for item in schedule.scheduleGroup:
            for id in item.scheduleId:
                if id not in schedule_ids:
                    schedule_ids.append(id)
        for item in schedule.scheduleName:
            for id in item.scheduleId:
                if id not in schedule_ids:
                    schedule_ids.append(id)
    return schedule_ids

def checkScheduleDetailedValidity(scheduleDetailed: ScheduleDetailed) -> bool | None:
    isEmpty = True
    for i in range(4)[1:]:
        emptyCabinet = (getattr(scheduleDetailed, f'cabinet{i}') == "" or getattr(scheduleDetailed, f'cabinet{i}') == "-")
        emptyTeacher = (getattr(scheduleDetailed, f'teacher{i}') == "" or getattr(scheduleDetailed, f'teacher{i}') == "-")
        emptyDiscipline = (getattr(scheduleDetailed, f'discipline{i}') == "" or getattr(scheduleDetailed, f'discipline{i}') == "-")
        if isEmpty:
            isEmpty = emptyCabinet and emptyTeacher and emptyDiscipline
        if (emptyCabinet ^ emptyTeacher) or (emptyDiscipline ^ emptyCabinet) or (emptyDiscipline ^ emptyTeacher):
            return False

    if isEmpty:
        return None
    else:
        return (scheduleDetailed.lessonNum != None)

# =================================================================================================================
# FlatScheduleDetailed-related stuff
# =================================================================================================================

def getScheduleIdByGroupAndDate(flatSchedule: FlatScheduleDetailed, currentDateId: int, currentGroupId: int) -> Optional[int]:
    scheduleId = None
    firstScheduleArray = getById_Array(currentDateId, flatSchedule.scheduleDay)
    secondScheduleArray = getById_Array(currentGroupId, flatSchedule.scheduleGroup)

    if firstScheduleArray is None or secondScheduleArray is None:
        return scheduleId

    for item in firstScheduleArray.scheduleId:
        if item in secondScheduleArray.scheduleId:
            scheduleId = item
            break

    return scheduleId

def moveDataFromScheduleToArray_Current(schedule: FlatScheduleDetailed, parameters: FlatScheduleParameters, scheduleId: int, detArray: List[ScheduleDetailed]):
    for item in schedule.cabinetLesson:
        if item.scheduleId == scheduleId:
            if 1 in item.subGroups:
                for subPair in item.subPairs:
                    detArray[(item.pairNum - 1) * 2 + (subPair - 1)].cabinet1 = \
                        getById(item.specialId, parameters.cabinetList).title

            if 2 in item.subGroups:
                for subPair in item.subPairs:
                    detArray[(item.pairNum - 1) * 2 + (subPair - 1)].cabinet2 = \
                        getById(item.specialId, parameters.cabinetList).title

            if 3 in item.subGroups:
                for subPair in item.subPairs:
                    detArray[(item.pairNum - 1) * 2 + (subPair - 1)].cabinet3 = \
                        getById(item.specialId, parameters.cabinetList).title

    for item in schedule.scheduleLesson:
        if item.scheduleId == scheduleId:
            if 1 in item.subGroups:
                for subPair in item.subPairs:
                    detArray[(item.pairNum - 1) * 2 + (subPair - 1)].discipline1 = \
                        getById(item.specialId, parameters.lessonList).title

            if 2 in item.subGroups:
                for subPair in item.subPairs:
                    detArray[(item.pairNum - 1) * 2 + (subPair - 1)].discipline2 = \
                        getById(item.specialId, parameters.lessonList).title

            if 3 in item.subGroups:
                for subPair in item.subPairs:
                    detArray[(item.pairNum - 1) * 2 + (subPair - 1)].discipline3 = \
                        getById(item.specialId, parameters.lessonList).title

    for item in schedule.teacherLesson:
        if item.scheduleId == scheduleId:
            if 1 in item.subGroups:
                for subPair in item.subPairs:
                    detArray[(item.pairNum - 1) * 2 + (subPair - 1)].teacher1 = \
                        getById(item.specialId, parameters.teacherList).title

            if 2 in item.subGroups:
                for subPair in item.subPairs:
                    detArray[(item.pairNum - 1) * 2 + (subPair - 1)].teacher2 = \
                        getById(item.specialId, parameters.teacherList).title

            if 3 in item.subGroups:
                for subPair in item.subPairs:
                    detArray[(item.pairNum - 1) * 2 + (subPair - 1)].teacher3 = \
                        getById(item.specialId, parameters.teacherList).title


def removeScheduleItemById_Current(flatSchedule: FlatScheduleDetailed, scheduleId: int, pairNum: Optional[int] = None, canRemoveScheduleId: bool = True):
    arrayToRemove: List[Data_IntIntIntArrayArray] = []

    for item in flatSchedule.scheduleLesson:
        if item.scheduleId == scheduleId and (item.pairNum == pairNum or pairNum is None):
            arrayToRemove.append(item)

    for item in arrayToRemove:
        flatSchedule.scheduleLesson.remove(item)

    arrayToRemove.clear()

    for item in flatSchedule.cabinetLesson:
        if item.scheduleId == scheduleId and (item.pairNum == pairNum or pairNum is None):
            arrayToRemove.append(item)

    for item in arrayToRemove:
        flatSchedule.cabinetLesson.remove(item)

    arrayToRemove.clear()

    for item in flatSchedule.teacherLesson:
        if item.scheduleId == scheduleId and (item.pairNum == pairNum or pairNum is None):
            arrayToRemove.append(item)

    for item in arrayToRemove:
        flatSchedule.teacherLesson.remove(item)

    if not canRemoveScheduleId:
        return

    for i in range(len(flatSchedule.scheduleLesson)):
        if flatSchedule.scheduleLesson[i].scheduleId == scheduleId:
            return

    for i in range(len(flatSchedule.cabinetLesson)):
        if flatSchedule.cabinetLesson[i].scheduleId == scheduleId:
            return

    for i in range(len(flatSchedule.teacherLesson)):
        if flatSchedule.teacherLesson[i].scheduleId == scheduleId:
            return

    secondArrayToRemove: List[Data_IntArray] = []

    for day in flatSchedule.scheduleDay:
        if day.scheduleId.__contains__(scheduleId):
            day.scheduleId.remove(scheduleId)
        if not day.scheduleId:  # Equivalent to being empty
            secondArrayToRemove.append(day)

    for item in secondArrayToRemove:
        flatSchedule.scheduleDay.remove(item)

    secondArrayToRemove.clear()

    for group in flatSchedule.scheduleGroup:
        if group.scheduleId.__contains__(scheduleId):
            group.scheduleId.remove(scheduleId)
        if not group.scheduleId:  # Equivalent to being empty
            secondArrayToRemove.append(group)

    for item in secondArrayToRemove:
        flatSchedule.scheduleGroup.remove(item)


def addPairToFlatSchedule_Current(flatSchedule: FlatScheduleDetailed, scheduleParameters: FlatScheduleParameters, scheduleId: int, pair: (ScheduleDetailed, ScheduleDetailed)):
    subPair1 = pair[0]
    subPair2 = pair[1]

    # print(f"Pair check 1: {subPair1.toJSON()}.")
    # print(f"Pair check 2: {subPair2.toJSON()}.")

    if (subPair1.lessonNum - 1) // 2 != (subPair2.lessonNum - 1) // 2:
        raise AssertionError(f"Provided subpairs are from different pairs! ({subPair1.lessonNum}, {subPair2.lessonNum})")

    lessonArray = []
    for subPair, subPairIndex in zip([subPair1, subPair2], [1, 2]):
        for i in range(1, 4):
            discipline = getattr(subPair, f"discipline{i}")
            if discipline and len(discipline) > 1:
                lessonArray.append(Data_IntIntIntArrayArray(
                    scheduleId,
                    (subPair.lessonNum - 1) // 2 + 1,
                    subPairs=[subPairIndex],
                    subGroups=[i],
                    specialId=getItemId_Title(scheduleParameters.lessonList, discipline)
                ))

    unifyScheduleArray(lessonArray)

    teacherArray = []
    for subPair, subPairIndex in zip([subPair1, subPair2], [1, 2]):
        for i in range(1, 4):
            teacher = getattr(subPair, f"teacher{i}")
            if teacher and len(teacher) > 1:
                teacherArray.append(Data_IntIntIntArrayArray(
                    scheduleId,
                    (subPair.lessonNum - 1) // 2 + 1,
                    subPairs=[subPairIndex],
                    subGroups=[i],
                    specialId=getItemId_Title(scheduleParameters.teacherList, teacher)
                ))

    unifyScheduleArray(teacherArray)

    cabinetArray = []
    for subPair, subPairIndex in zip([subPair1, subPair2], [1, 2]):
        for i in range(1, 4):
            cabinet = getattr(subPair, f"cabinet{i}")
            if cabinet and len(cabinet) > 1:
                cabinetArray.append(Data_IntIntIntArrayArray(
                    scheduleId,
                    (subPair.lessonNum - 1) // 2 + 1,
                    subPairs=[subPairIndex],
                    subGroups=[i],
                    specialId=getItemId_Title(scheduleParameters.cabinetList, cabinet)
                ))

    unifyScheduleArray(cabinetArray)

    flatSchedule.scheduleLesson.extend(lessonArray)
    flatSchedule.teacherLesson.extend(teacherArray)
    flatSchedule.cabinetLesson.extend(cabinetArray)



def changeSingleScheduleDay_Current(baseSchedule: FlatScheduleDetailed, newSchedule: FlatScheduleDetailed, dateId: int) -> FlatScheduleDetailed:
    returnSchedule = copy.deepcopy(baseSchedule)

    dateIdArray = getById_Array(dateId, newSchedule.scheduleDay)
    if dateIdArray is not None:
        for scheduleId in dateIdArray.scheduleId:
            for newGroup in newSchedule.scheduleGroup:
                if scheduleId in newGroup.scheduleId:
                    for baseGroup in returnSchedule.scheduleGroup:
                        if baseGroup.specialId == newGroup.specialId:
                            if scheduleId not in baseGroup.scheduleId:
                                baseGroup.scheduleId.append(scheduleId)

    returnSchedule_dateIdArray = getById_Array(dateId, returnSchedule.scheduleDay)
    if returnSchedule_dateIdArray is not None:
        arrayToRemove = []
        for scheduleId in returnSchedule_dateIdArray.scheduleId:
            if scheduleId not in arrayToRemove:
                arrayToRemove.append(scheduleId)

        for scheduleId in arrayToRemove:
            removeScheduleItemById_Current(returnSchedule, scheduleId, canRemoveScheduleId=(dateIdArray is None))

        if dateIdArray is not None:
            returnSchedule_dateIdArray.scheduleId = list(dateIdArray.scheduleId)  # Clone the list
    elif dateIdArray is not None:
        returnSchedule.scheduleDay.append(Data_IntArray(dateId, list(dateIdArray.scheduleId)))  # Clone the list

    if dateIdArray is not None:
        for scheduleId in dateIdArray.scheduleId:
            removeScheduleItemById_Current(returnSchedule, scheduleId, canRemoveScheduleId=False)

            for groupIdArray in newSchedule.scheduleGroup:
                if groupIdArray.scheduleId.__contains__(scheduleId):
                    returnSchedule_groupIdArray = getById_Array(groupIdArray.specialId, returnSchedule.scheduleGroup)
                    if returnSchedule_groupIdArray == None:
                        returnSchedule_groupIdArray = Data_IntArray(groupIdArray.specialId, [])
                        returnSchedule.scheduleGroup.append(returnSchedule_groupIdArray)
                    if not returnSchedule_groupIdArray.scheduleId.__contains__(scheduleId):
                        returnSchedule_groupIdArray.scheduleId.append(scheduleId)

            for lesson in newSchedule.scheduleLesson:
                if lesson.scheduleId == scheduleId:
                    returnSchedule.scheduleLesson.append(copy.deepcopy(lesson))
            for teacher in newSchedule.teacherLesson:
                if teacher.scheduleId == scheduleId:
                    returnSchedule.teacherLesson.append(copy.deepcopy(teacher))
            for cabinet in newSchedule.cabinetLesson:
                if cabinet.scheduleId == scheduleId:
                    returnSchedule.cabinetLesson.append(copy.deepcopy(cabinet))

    return returnSchedule

# ================================================================================================================
# FlatScheduleBase-related stuff
# ================================================================================================================

def getScheduleIdByGroupDateAndBaseScheduleId(flatSchedule: FlatScheduleBase, currentDateId: int, currentGroupId: int, baseScheduleId: int) -> Optional[int]:
    scheduleId = None
    firstScheduleArray = getById_Array(currentDateId, flatSchedule.scheduleDay)
    secondScheduleArray = getById_Array(currentGroupId, flatSchedule.scheduleGroup)
    thirdScheduleArray = getById_Array(baseScheduleId, flatSchedule.scheduleName)

    if firstScheduleArray is None or secondScheduleArray is None or thirdScheduleArray is None:
        return scheduleId

    for item in firstScheduleArray.scheduleId:
        if item in secondScheduleArray.scheduleId and item in thirdScheduleArray.scheduleId:
            scheduleId = item
            break

    return scheduleId

def moveDataFromScheduleToArray_Base(schedule: FlatScheduleBase, parameters: FlatScheduleParameters, scheduleId: int, detArray: List[ScheduleDetailed]):
    moveDataFromScheduleToArray_Current(FlatScheduleDetailed(
        scheduleDay=schedule.scheduleDay,
        scheduleGroup=schedule.scheduleGroup,
        scheduleLesson=schedule.scheduleLesson,
        teacherLesson=schedule.teacherLesson,
        cabinetLesson=schedule.cabinetLesson
    ), parameters, scheduleId, detArray)

def removeScheduleItemById_Base(flatSchedule: FlatScheduleBase, scheduleId: int, pairNum: Optional[int] = None, canRemoveScheduleId: bool = True):
    removeScheduleItemById_Current(FlatScheduleDetailed(
        scheduleDay=flatSchedule.scheduleDay,
        scheduleGroup=flatSchedule.scheduleGroup,
        scheduleLesson=flatSchedule.scheduleLesson,
        teacherLesson=flatSchedule.teacherLesson,
        cabinetLesson=flatSchedule.cabinetLesson
    ), scheduleId, pairNum, canRemoveScheduleId)

    if not canRemoveScheduleId:
        return

    for item in flatSchedule.scheduleDay:
        if scheduleId in item.scheduleId:
            return

    for item in flatSchedule.scheduleGroup:
        if scheduleId in item.scheduleId:
            return

    for i in range(len(flatSchedule.scheduleName)):
        if scheduleId in flatSchedule.scheduleName[i].scheduleId:
            flatSchedule.scheduleName[i].scheduleId.remove(scheduleId)
            if not flatSchedule.scheduleName[i].scheduleId:
                # If scheduleName list is empty, remove the schedule
                flatSchedule.scheduleName.pop(i)
            break

def addPairToFlatSchedule_Base(flatSchedule: FlatScheduleBase, scheduleParameters: FlatScheduleParameters, scheduleId: int, pair: (ScheduleDetailed, ScheduleDetailed)):
    addPairToFlatSchedule_Current(FlatScheduleDetailed(
        scheduleDay=flatSchedule.scheduleDay,
        scheduleGroup=flatSchedule.scheduleGroup,
        scheduleLesson=flatSchedule.scheduleLesson,
        teacherLesson=flatSchedule.teacherLesson,
        cabinetLesson=flatSchedule.cabinetLesson
    ), scheduleParameters, scheduleId, pair)


def changeSingleScheduleDay_Base(dateId: int, baseSchedule: FlatScheduleBase, newSchedule: FlatScheduleBase, nameId: int) -> FlatScheduleBase:
    returnSchedule = copy.deepcopy(baseSchedule)

    dateIdArray = getById_Array(dateId, newSchedule.scheduleDay)
    nameIdArray = getById_Array(nameId, newSchedule.scheduleName)

    if dateIdArray is not None and nameIdArray is not None:
        for scheduleId in nameIdArray.scheduleId:
            if scheduleId in dateIdArray.scheduleId:
                for newGroup in newSchedule.scheduleGroup:
                    if scheduleId in newGroup.scheduleId:
                        for baseGroup in returnSchedule.scheduleGroup:
                            if baseGroup.specialId == newGroup.specialId:
                                if scheduleId not in baseGroup.scheduleId:
                                    baseGroup.scheduleId.append(scheduleId)

    returnSchedule_dateIdArray = getById_Array(dateId, returnSchedule.scheduleDay)
    returnSchedule_nameIdArray = getById_Array(nameId, returnSchedule.scheduleName)

    if returnSchedule_nameIdArray is not None:
        arrayToRemove = []
        for scheduleId in returnSchedule_nameIdArray.scheduleId:
            if returnSchedule_dateIdArray is not None and scheduleId in returnSchedule_dateIdArray.scheduleId:
                if scheduleId not in arrayToRemove:
                    arrayToRemove.append(scheduleId)

        for scheduleId in arrayToRemove:
            removeScheduleItemById_Base(returnSchedule, scheduleId, canRemoveScheduleId=(dateIdArray is None or nameIdArray is None))

        if dateIdArray is not None and nameIdArray is not None:
            for scheduleId in nameIdArray.scheduleId:
                if scheduleId in dateIdArray.scheduleId:
                    if returnSchedule_dateIdArray is None:
                        returnSchedule_dateIdArray = Data_IntArray(dateId)
                        returnSchedule.scheduleDay.append(returnSchedule_dateIdArray)
                    if scheduleId not in returnSchedule_dateIdArray.scheduleId:
                        returnSchedule_dateIdArray.scheduleId.append(scheduleId)
                    if returnSchedule_nameIdArray is None:
                        returnSchedule_nameIdArray = Data_IntArray(nameId)
                        returnSchedule.scheduleName.append(returnSchedule_nameIdArray)
                    if scheduleId not in returnSchedule_nameIdArray.scheduleId:
                        returnSchedule_nameIdArray.scheduleId.append(scheduleId)
    elif dateIdArray is not None and nameIdArray is not None:
        for scheduleId in nameIdArray.scheduleId:
            if scheduleId in dateIdArray.scheduleId:
                if returnSchedule_dateIdArray is None:
                    returnSchedule_dateIdArray = Data_IntArray(dateId)
                    returnSchedule.scheduleDay.append(returnSchedule_dateIdArray)
                if scheduleId not in returnSchedule_dateIdArray.scheduleId:
                    returnSchedule_dateIdArray.scheduleId.append(scheduleId)
                if returnSchedule_nameIdArray is None:
                    returnSchedule_nameIdArray = Data_IntArray(nameId)
                    returnSchedule.scheduleName.append(returnSchedule_nameIdArray)
                if scheduleId not in returnSchedule_nameIdArray.scheduleId:
                    returnSchedule_nameIdArray.scheduleId.append(scheduleId)

    if nameIdArray is not None:
        for scheduleId in nameIdArray.scheduleId:
            if dateIdArray is not None and scheduleId in dateIdArray.scheduleId:
                removeScheduleItemById_Base(returnSchedule, scheduleId, canRemoveScheduleId=False)

                for groupIdArray in newSchedule.scheduleGroup:
                    if groupIdArray.scheduleId.__contains__(scheduleId):
                        returnSchedule_groupIdArray = getById_Array(groupIdArray.specialId, returnSchedule.scheduleGroup)
                        if returnSchedule_groupIdArray == None:
                            returnSchedule_groupIdArray = Data_IntArray(groupIdArray.specialId, [])
                            returnSchedule.scheduleGroup.append(returnSchedule_groupIdArray)
                        if not returnSchedule_groupIdArray.scheduleId.__contains__(scheduleId):
                            returnSchedule_groupIdArray.scheduleId.append(scheduleId)

                for lesson in newSchedule.scheduleLesson:
                    if lesson.scheduleId == scheduleId:
                        returnSchedule.scheduleLesson.append(copy.deepcopy(lesson))
                for teacher in newSchedule.teacherLesson:
                    if teacher.scheduleId == scheduleId:
                        returnSchedule.teacherLesson.append(copy.deepcopy(teacher))
                for cabinet in newSchedule.cabinetLesson:
                    if cabinet.scheduleId == scheduleId:
                        returnSchedule.cabinetLesson.append(copy.deepcopy(cabinet))

    return returnSchedule

def applyBaseScheduleByNameAndDate(flatSchedule: FlatScheduleDetailed, dateId: int, baseSchedule: FlatScheduleBase, nameId: int, dayId: int):
    base_dayIdArray = getById_Array(dayId, baseSchedule.scheduleDay)
    base_nameIdArray = getById_Array(nameId, baseSchedule.scheduleName)

    if base_dayIdArray is None or base_nameIdArray is None:
        print("ADMIN_BASE_SCHEDULE_APPLICATION: No IDs to apply for that day and base schedule name.")
        return

    idsToApply = []
    for it in base_nameIdArray.scheduleId:
        if it in base_dayIdArray.scheduleId:
            idsToApply.append(it)

    if not idsToApply:
        print("ADMIN_BASE_SCHEDULE_APPLICATION: No IDs to apply for that day and base schedule name.")
        return

    dateIdArray = getById_Array(dateId, flatSchedule.scheduleDay)
    if dateIdArray is None:
        dateIdArray = Data_IntArray(dateId)
        flatSchedule.scheduleDay.append(dateIdArray)

    for scheduleId in idsToApply:
        base_groupIdArray = None
        for group in baseSchedule.scheduleGroup:
            if scheduleId in group.scheduleId:
                base_groupIdArray = group
                break

        if base_groupIdArray is None:
            raise AssertionError("Found a schedule ID with no group attached to it! Something is definitely wrong with the DB.")

        groupIdArray = getById_Array(base_groupIdArray.specialId, flatSchedule.scheduleGroup)
        if groupIdArray is None:
            groupIdArray = Data_IntArray(base_groupIdArray.specialId)
            flatSchedule.scheduleGroup.append(groupIdArray)

        sameIdInFlatSchedule = None
        for it in dateIdArray.scheduleId:
            if it in groupIdArray.scheduleId:
                sameIdInFlatSchedule = it
                break

        if sameIdInFlatSchedule is None:
            totalIdsList = list(set(groupIdArray.scheduleId) | set(dateIdArray.scheduleId))
            sameIdInFlatSchedule = getEmptyId(totalIdsList)

            groupIdArray.scheduleId.append(sameIdInFlatSchedule)
            dateIdArray.scheduleId.append(sameIdInFlatSchedule)
        else:
            removeScheduleItemById_Current(flatSchedule, sameIdInFlatSchedule, canRemoveScheduleId=False)

        for lesson in baseSchedule.scheduleLesson:
            if lesson.scheduleId == scheduleId:
                duplicateItem = copy.deepcopy(lesson)
                duplicateItem.scheduleId = sameIdInFlatSchedule
                flatSchedule.scheduleLesson.append(duplicateItem)

        for lesson in baseSchedule.cabinetLesson:
            if lesson.scheduleId == scheduleId:
                duplicateItem = copy.deepcopy(lesson)
                duplicateItem.scheduleId = sameIdInFlatSchedule
                flatSchedule.cabinetLesson.append(duplicateItem)

        for lesson in baseSchedule.teacherLesson:
            if lesson.scheduleId == scheduleId:
                duplicateItem = copy.deepcopy(lesson)
                duplicateItem.scheduleId = sameIdInFlatSchedule
                flatSchedule.teacherLesson.append(duplicateItem)

        if not groupIdArray.scheduleId:
            flatSchedule.scheduleGroup.remove(groupIdArray)

    if not dateIdArray.scheduleId:
        flatSchedule.scheduleDay.remove(dateIdArray)

# ================================================================================================================
# Conversions
# ================================================================================================================

def unifyScheduleArray(scheduleItemArray: List[Data_IntIntIntArrayArray]):
    arrayToRemove = []

    currentIndex = 0
    while currentIndex < len(scheduleItemArray):
        for i in range(len(scheduleItemArray)):
            if (scheduleItemArray[i].specialId == scheduleItemArray[currentIndex].specialId and currentIndex != i):

                # print("")
                # print(f"Current-subp = {scheduleItemArray[currentIndex].subPairs}, i-subp = {scheduleItemArray[i].subPairs}")
                # print(f"Are they the same? {scheduleItemArray[currentIndex].subPairs == scheduleItemArray[i].subPairs}")
                if checkIfItemArraysAreEqual(scheduleItemArray[currentIndex].subPairs,
                                             scheduleItemArray[i].subPairs):
                    for item in scheduleItemArray[i].subGroups:
                        if item not in scheduleItemArray[currentIndex].subGroups:
                            scheduleItemArray[currentIndex].subGroups.append(item)

                # print("")
                # print(f"Current-subg = {scheduleItemArray[currentIndex].subGroups}, i-subg = {scheduleItemArray[i].subGroups}")
                # print(f"Are they the same? {scheduleItemArray[currentIndex].subGroups == scheduleItemArray[i].subGroups}")
                if checkIfItemArraysAreEqual(scheduleItemArray[currentIndex].subGroups, scheduleItemArray[i].subGroups):
                    for item in scheduleItemArray[i].subPairs:
                        if item not in scheduleItemArray[currentIndex].subPairs:
                            scheduleItemArray[currentIndex].subPairs.append(item)

                if (checkIfItemArraysAreEqual(scheduleItemArray[currentIndex].subPairs, scheduleItemArray[i].subPairs) or
                        checkIfItemArraysAreEqual(scheduleItemArray[currentIndex].subGroups, scheduleItemArray[i].subGroups)):
                    arrayToRemove.append(scheduleItemArray[i])

        for it in arrayToRemove:
            if scheduleItemArray.index(it) < currentIndex:
                currentIndex -= 1
            scheduleItemArray.remove(it)

        arrayToRemove.clear()
        currentIndex += 1

# =================================================================================================================
# Database-related stuff
# =================================================================================================================

def convertFlatScheduleModelToDict(schedule: Model_FlatSchedule) -> ReturnDict:
    returnSchedule = FlatSchedule(BaseParameters = schedule.BaseParameters[0], BaseSchedules = schedule.BaseSchedules[0], CurrentSchedules = schedule.CurrentSchedules[0])
    returnSchedule.BaseParameters[getParametersIdentifier(APP_TYPEID_PARAMETERS_DATE)] = getDayListData()
    newDict = json.loads(returnSchedule.toJSON())
    return newDict

def getDateIndex(date: Date)->int:
    index = -1
    for i in range(MOBILE_APP_PAGE_COUNT):
        if getDateWithOffset(i) == date:
            index = i
            break
    return index

def getDateWithOffset(index: int) -> Date:
    position = index - MOBILE_APP_PAGE_COUNT // 2
    c = datetime.datetime.now()

    if position != 0:
        c += datetime.timedelta(days=position)

    year = c.year
    month = c.month
    day = c.day
    return Date(year=year, month=month, day=day)

def cleanScheduleFromUnnecessaryDates(flatSchedule: FlatScheduleDetailed, dayList: list[Data_IntDate]):
    arrayToRemove = []
    for curData in flatSchedule.scheduleDay:
        curDate = getById(curData.specialId, dayList)
        if curDate is None:
            for it in curData.scheduleId:
                if it not in arrayToRemove:
                    arrayToRemove.append(it)

    for it in arrayToRemove:
        removeScheduleItemById_Current(flatSchedule, it)

def updateDayList():
    dayList = getDayListData()

    for i in range(MOBILE_APP_PAGE_COUNT):
        date = getDateWithOffset(i)
        # print(f"Current date: {date}.")
        date_exists = False
        for item in dayList:
            if item.date == date:
                date_exists = True
                break

        if not date_exists:
            new_index = getPossibleId_Date(dayList)
            # print(f"Appending data: {Data_IntDate(new_index, date)}.")
            dayList.append(Data_IntDate(new_index, date))

    arrayToRemove = []
    for item in dayList:
        if getDateIndex(item.date) == -1:
            arrayToRemove.append(item)

    for item in arrayToRemove:
        # print(f"Removing data: {item}.")
        dayList.remove(item)

    schedule = getSavedSchedule()
    currentSchedule = getDataFromDictGeneric(schedule.CurrentSchedules[0])
    currentScheduleStaged = getDataFromDictGeneric(schedule.CurrentSchedules[1])

    if len(arrayToRemove) > 0:
        cleanScheduleFromUnnecessaryDates(currentSchedule, dayList)
        cleanScheduleFromUnnecessaryDates(currentScheduleStaged, dayList)
    arrayToRemove.clear()

    # print(f"Day list after edits: {dayList}.")
    for i in range(len(dayList)):
        dayList[i] = json.loads(Data_IntDate(dayList[i].id, f"{dayList[i].date.year}-{dayList[i].date.month}-{dayList[i].date.day}").toJSON())

    schedule.BaseParameters[0][getParametersIdentifier(APP_TYPEID_PARAMETERS_DATE)] = dayList
    schedule.CurrentSchedules = [json.loads(currentSchedule.toJSON()), json.loads(currentScheduleStaged.toJSON())]
    schedule.save()

def checkIfParameterIsNecessary(typeId: int, paramId: int) -> bool:
    schedule = getSavedSchedule()
    scheduleCurrent = getDataFromDictGeneric(schedule.CurrentSchedules[0])
    scheduleBase = getDataFromDictGeneric(schedule.BaseSchedules[0])
    scheduleCurrentStaged = getDataFromDictGeneric(schedule.CurrentSchedules[1])
    scheduleBaseStaged = getDataFromDictGeneric(schedule.BaseSchedules[1])

    listToCheck = []
    if typeId == APP_TYPEID_PARAMETERS_DISCIPLINE:
        listToCheck.extend(scheduleCurrent.scheduleLesson)
        listToCheck.extend(scheduleBase.scheduleLesson)
        listToCheck.extend(scheduleCurrentStaged.scheduleLesson)
        listToCheck.extend(scheduleBaseStaged.scheduleLesson)
    elif typeId == APP_TYPEID_PARAMETERS_TEACHER:
        listToCheck.extend(scheduleCurrent.teacherLesson)
        listToCheck.extend(scheduleBase.teacherLesson)
        listToCheck.extend(scheduleCurrentStaged.teacherLesson)
        listToCheck.extend(scheduleBaseStaged.teacherLesson)
    elif typeId == APP_TYPEID_PARAMETERS_GROUP:
        listToCheck.extend(scheduleCurrent.scheduleGroup)
        listToCheck.extend(scheduleBase.scheduleGroup)
        listToCheck.extend(scheduleCurrentStaged.scheduleGroup)
        listToCheck.extend(scheduleBaseStaged.scheduleGroup)
    elif typeId == APP_TYPEID_PARAMETERS_CABINET:
        listToCheck.extend(scheduleCurrent.cabinetLesson)
        listToCheck.extend(scheduleBase.cabinetLesson)
        listToCheck.extend(scheduleCurrentStaged.cabinetLesson)
        listToCheck.extend(scheduleBaseStaged.cabinetLesson)
    else:
        raise ValueError("Unknown TypeID was supplied (Parameter necessity check function)!")

    for it in listToCheck:
        if it.specialId == paramId:
            return True
    return False

# ================================================================================================================
# Comparison-related stuff
# ================================================================================================================

def checkIfScheduleDetailedEquals(item1: ScheduleDetailed, item2: ScheduleDetailed) -> bool:
    return (item1.discipline1 == item2.discipline1 and
            item1.teacher1 == item2.teacher1 and
            item1.cabinet1 == item2.cabinet1 and
            item1.discipline2 == item2.discipline2 and
            item1.teacher2 == item2.teacher2 and
            item1.cabinet2 == item2.cabinet2 and
            item1.discipline3 == item2.discipline3 and
            item1.teacher3 == item2.teacher3 and
            item1.cabinet3 == item2.cabinet3)


def checkIfItemArraysAreEqual(itemArray1, itemArray2) -> bool:
    if len(itemArray1) != len(itemArray2):
        return False
    for item in itemArray1:
        if item not in itemArray2:
            return False
    for item in itemArray2:
        if item not in itemArray1:
            return False
    return True

def checkIfFlatScheduleDetailedEquals(flatSchedule1: FlatScheduleDetailed, flatSchedule2: FlatScheduleDetailed):
    return (checkIfItemArraysAreEqual(flatSchedule1.scheduleLesson, flatSchedule2.scheduleLesson) and
            checkIfItemArraysAreEqual(flatSchedule1.teacherLesson, flatSchedule2.teacherLesson) and
            checkIfItemArraysAreEqual(flatSchedule1.cabinetLesson, flatSchedule2.cabinetLesson) and
            checkIfItemArraysAreEqual(flatSchedule1.scheduleDay, flatSchedule2.scheduleDay) and
            checkIfItemArraysAreEqual(flatSchedule1.scheduleGroup, flatSchedule2.scheduleGroup))

def checkIfFlatScheduleBaseEquals(flatSchedule1: FlatScheduleBase, flatSchedule2: FlatScheduleBase, should_check_name_list: bool):
    return ((not should_check_name_list or checkIfItemArraysAreEqual(flatSchedule1.nameList, flatSchedule2.nameList)) and
            checkIfItemArraysAreEqual(flatSchedule1.scheduleName, flatSchedule2.scheduleName) and
            checkIfItemArraysAreEqual(flatSchedule1.scheduleLesson, flatSchedule2.scheduleLesson) and
            checkIfItemArraysAreEqual(flatSchedule1.teacherLesson, flatSchedule2.teacherLesson) and
            checkIfItemArraysAreEqual(flatSchedule1.cabinetLesson, flatSchedule2.cabinetLesson) and
            checkIfItemArraysAreEqual(flatSchedule1.scheduleDay, flatSchedule2.scheduleDay) and
            checkIfItemArraysAreEqual(flatSchedule1.scheduleGroup, flatSchedule2.scheduleGroup))
