import copy
import json
import time

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .constants import APP_PAIR_MAX_AMOUNT
from .data import FlatScheduleParameters, FlatScheduleBase, FlatScheduleDetailed, Data_IntString, Data_IntArray, \
    ScheduleDetailed, FlatScheduleResponse
from .models import Model_FlatSchedule
from .utils import convertFlatScheduleModelToDict, updateDayList, changeSingleScheduleDay_Current, \
    changeSingleScheduleDay_Base, getDataFromDictGeneric, \
    checkIfParameterIsNecessary, getSavedSchedule, getParametersIdentifier, getById, getScheduleIdByGroupAndDate, \
    getEmptyId, collectAllCurrentScheduleIds, removeScheduleItemById_Current, addPairToFlatSchedule_Current, \
    getScheduleIdByGroupDateAndBaseScheduleId, collectAllBaseScheduleIds, removeScheduleItemById_Base, \
    addPairToFlatSchedule_Base, checkIfFlatScheduleDetailedEquals, checkIfFlatScheduleBaseEquals, getPossibleId_String, \
    applyBaseScheduleByNameAndDate, getById_Array, checkScheduleDetailedValidity


@api_view(['GET'])
def getRoutes(request):
    routes = [
        {
            'Endpoint': '/schedule/',
            'method': 'GET',
            'body': None,
            'description': 'Returns the entire FlatSchedule object'
        },
        {
            'Endpoint': 'schedule/parameters/',
            'method': 'GET',
            'body': None,
            'description': 'Returns FlatScheduleParameters object'
        },
        {
            'Endpoint': 'schedule/parameters/id/',
            'method': 'GET',
            'body': None,
            'description': 'Returns a specific parameter list'
        },
        {
            'Endpoint': '/schedule/current/date',
            'method': 'GET',
            'body': None,
            'description': 'Returns staged and main FlatScheduleDetailed objects, plus comparison results'
        },
        {
            'Endpoint': '/schedule/base/name/day',
            'method': 'GET',
            'body': None,
            'description': 'Returns staged and main FlatScheduleBase objects, plus comparison results'
        },
        {
            'Endpoint': '/schedule/parameters/id/upload/',
            'method': 'PUT',
            'body': [],
            'description': 'Uploads a specific parameter list'
        },
        {
            'Endpoint': '/schedule/current/stagepair/group/date/',
            'method': 'PUT',
            'body': ({'lessonNum': 0,'discipline1': "",'cabinet1': "",'teacher1': "",'discipline2': "",'cabinet2': "",'teacher2': "",'discipline3': "",'cabinet3': "",'teacher3': ""},
                     {'lessonNum': 0,'discipline1': "",'cabinet1': "",'teacher1': "",'discipline2': "",'cabinet2': "",'teacher2': "",'discipline3': "",'cabinet3': "",'teacher3': ""}),
            'description': 'Stages changes to a single pair in FlatScheduleDetailed object'
        },
        {
            'Endpoint': '/schedule/current/applybase/name/day/date/',
            'method': 'PUT',
            'body': None,
            'description': 'Applies a base schedule to a date in FlatScheduleCurrent object'
        },
        {
            'Endpoint': '/schedule/base/stagepair/group/date/name/',
            'method': 'PUT',
            'body': ({'lessonNum': 0,'discipline1': "",'cabinet1': "",'teacher1': "",'discipline2': "",'cabinet2': "",'teacher2': "",'discipline3': "",'cabinet3': "",'teacher3': ""},
                     {'lessonNum': 0,'discipline1': "",'cabinet1': "",'teacher1': "",'discipline2': "",'cabinet2': "",'teacher2': "",'discipline3': "",'cabinet3': "",'teacher3': ""}),
            'description': 'Stages changes to a single pair in FlatScheduleBase object'
        },
        {
            'Endpoint': '/schedule/base/stageschedule/',
            'method': 'PUT',
            'body': {'id': 0, 'title': ""},
            'description': 'Stages changes to a list of base schedules in FlatScheduleBase object'
        },
        {
            'Endpoint': '/schedule/current/apply/date/updateVersion',
            'method': 'PUT',
            'body': None,
            'description': 'Applies date-based (or all) staged changes to the main FlatScheduleCurrent object'
        },
        {
            'Endpoint': '/schedule/base/apply/day/name',
            'method': 'PUT',
            'body': None,
            'description': 'Applies day-based (or all) staged changes to the main FlatScheduleBase object'
        },
        {
            'Endpoint': '/schedule/current/reset/date',
            'method': 'PUT',
            'body': None,
            'description': 'Resets date-based (or all) staged changes to the main FlatScheduleCurrent object'
        },
        {
            'Endpoint': '/schedule/base/reset/day/name',
            'method': 'PUT',
            'body': None,
            'description': 'Resets day-based (or all) staged changes to the main FlatScheduleBase object'
        },
    ]
    return Response(routes)

# Create your views here.

@api_view(['GET'])
def getSchedule(request):
    updateDayList()
    schedule = getSavedSchedule()
    return Response(convertFlatScheduleModelToDict(schedule))

@api_view(['GET'])
def getScheduleParameters(request):
    updateDayList()
    schedule = getSavedSchedule()
    parameters = getDataFromDictGeneric(schedule.BaseParameters[0])
    return Response(json.loads(parameters.toJSON()))

@api_view(['GET'])
def getScheduleParametersSpecific(request, pk):
    pk = int(pk)

    updateDayList()
    schedule = getSavedSchedule()
    parameters = schedule.BaseParameters[0][getParametersIdentifier(pk, False)]
    return Response(parameters)

@api_view(['GET'])
def getScheduleVersion(request):
    updateDayList()
    schedule = getSavedSchedule()
    scheduleData = getDataFromDictGeneric(schedule.CurrentSchedules[0])
    return scheduleData.version

@api_view(['GET'])
def getScheduleCurrent(request, pk):
    pk = int(pk)
    updateDayList()

    schedule = getSavedSchedule()
    scheduleData = getDataFromDictGeneric(schedule.CurrentSchedules[0])
    scheduleStagedData = getDataFromDictGeneric(schedule.CurrentSchedules[1])

    schedulesAreSame = checkIfFlatScheduleDetailedEquals(scheduleData, scheduleStagedData)
    if pk == -1:
        schedulesAreSame_Day = None
    else:
        schedulesAreSame_Day = checkIfFlatScheduleDetailedEquals(changeSingleScheduleDay_Current(baseSchedule=scheduleData, newSchedule=scheduleStagedData, dateId=pk), scheduleData)
        if (schedulesAreSame and not schedulesAreSame_Day):
            raise AssertionError("Data mismatch: schedules are same, but not on a specific day (getScheduleCurrent).")

    response = FlatScheduleResponse(scheduleData, scheduleStagedData, schedulesAreSame, schedulesAreSame_Day)
    return Response(json.loads(response.toJSON()))

@api_view(['GET'])
def getScheduleBase(request, pk1, pk2):
    pk1 = int(pk1); pk2 = int(pk2)
    updateDayList()

    schedule = getSavedSchedule()
    scheduleData = getDataFromDictGeneric(schedule.BaseSchedules[0])
    scheduleStagedData = getDataFromDictGeneric(schedule.BaseSchedules[1])

    schedulesAreSame = checkIfFlatScheduleBaseEquals(scheduleData, scheduleStagedData, True)
    if pk1 == -1 or pk2 == -1:
        schedulesAreSame_Day = None
    else:
        schedulesAreSame_Day = checkIfFlatScheduleBaseEquals(changeSingleScheduleDay_Base(nameId=pk1, dateId=pk2, baseSchedule=scheduleData, newSchedule=scheduleStagedData), scheduleData, False)
        if (schedulesAreSame and not schedulesAreSame_Day):
            raise AssertionError("Data mismatch: schedules are same, but not on a specific day (getScheduleBase).")

    response = FlatScheduleResponse(scheduleData, scheduleStagedData, schedulesAreSame, schedulesAreSame_Day)
    return Response(json.loads(response.toJSON()))

@api_view(['PUT'])
def uploadScheduleParameters(request, pk):
    pk = int(pk)

    data = request.data
    identifier = getParametersIdentifier(pk, False)
    schedule = getSavedSchedule()

    listOfNewTitles = []
    for item in data:
        if listOfNewTitles.__contains__(item['title']):
            raise AssertionError("Found same titles in parameters list (uploadScheduleParameters).")
        listOfNewTitles.append(item['title'])
    listOfNewTitles.clear()

    listOfCurrentIds = []
    for item in schedule.BaseParameters[0][identifier]:
        listOfCurrentIds.append(item['id'])
    listOfNewIds = []
    for item in data:
        listOfNewIds.append(item['id'])

    for id in listOfCurrentIds:
        if not listOfNewIds.__contains__(id):
            if checkIfParameterIsNecessary(pk, id):
                raise AssertionError(f"Tried to delete a useful ID (uploadScheduleParameters): {id}.")

    schedule.BaseParameters[0][identifier] = data
    schedule.save()

    return Response(True)

@api_view(['PUT'])
def stageCurrentSchedulePair(request, pk1, pk2):
    pk1 = int(pk1); pk2 = int(pk2)

    data = request.data
    if 'first' in data:
        scheduleDetailed1 = getDataFromDictGeneric(data['first'])
    else:
        scheduleDetailed1 = ScheduleDetailed()
    if 'second' in data:
        scheduleDetailed2 = getDataFromDictGeneric(data['second'])
    else:
        scheduleDetailed2 = ScheduleDetailed()

    if (checkScheduleDetailedValidity(scheduleDetailed1) == False or checkScheduleDetailedValidity(scheduleDetailed2) == False):
        raise ValueError(f"Supplied with incorrect data (uploadCurrentSchedulePair): {data}.")
    elif scheduleDetailed1.lessonNum == None or scheduleDetailed2.lessonNum == None:
        raise ValueError(f"Supplied with no lesson number (uploadCurrentSchedulePair): {data}.")
    elif abs(scheduleDetailed1.lessonNum - scheduleDetailed2.lessonNum) != 1 or int((scheduleDetailed1.lessonNum - 1) / 2) != int((scheduleDetailed2.lessonNum - 1) / 2):
        raise ValueError(f"Supplied with sub-pairs from different pairs (uploadCurrentSchedulePair): {data}.")

    if checkScheduleDetailedValidity(scheduleDetailed1) == None:
        scheduleDetailed1 = ScheduleDetailed(scheduleDetailed1.lessonNum)
    if checkScheduleDetailedValidity(scheduleDetailed2) == None:
        scheduleDetailed2 = ScheduleDetailed(scheduleDetailed2.lessonNum)
    pairNum = int(scheduleDetailed1.lessonNum / 2)

    schedule = getSavedSchedule()
    parameters = getDataFromDictGeneric(schedule.BaseParameters[0])

    if getById(pk1, parameters.groupList) == None:
        raise ValueError(f"Unknown group Id (uploadCurrentSchedulePair): {pk1}.")
    if getById(pk2, parameters.dayList) == None:
        raise ValueError(f"Unknown date Id (uploadCurrentSchedulePair): {pk2}.")
    if not pairNum in range(APP_PAIR_MAX_AMOUNT):
        raise ValueError(f"Wrong pair number (uploadCurrentSchedulePair): {pairNum}.")

    currentScheduleMain = getDataFromDictGeneric(schedule.CurrentSchedules[0])
    currentScheduleStaged = getDataFromDictGeneric(schedule.CurrentSchedules[1])

    if getById_Array(pk2, currentScheduleStaged.scheduleDay) is None:
        currentScheduleStaged.scheduleDay.append(Data_IntArray(pk2, []))
    if getById_Array(pk1, currentScheduleStaged.scheduleGroup) is None:
        currentScheduleStaged.scheduleGroup.append(Data_IntArray(pk1, []))

    scheduleId = getScheduleIdByGroupAndDate(currentScheduleStaged, pk2, pk1)
    chosenScheduleIdIsNew = (scheduleId is None)

    if chosenScheduleIdIsNew:
        scheduleId = getScheduleIdByGroupAndDate(currentScheduleMain, pk2, pk1)
        if scheduleId is None:
            scheduleId = getEmptyId(collectAllCurrentScheduleIds())
        day_schedule_array = getById_Array(pk2, currentScheduleStaged.scheduleDay)
        group_schedule_array = getById_Array(pk1, currentScheduleStaged.scheduleGroup)

        day_schedule_array.scheduleId.append(scheduleId)
        group_schedule_array.scheduleId.append(scheduleId)

    if checkScheduleDetailedValidity(scheduleDetailed1) == None and checkScheduleDetailedValidity(scheduleDetailed2) == None:
        removeScheduleItemById_Current(currentScheduleStaged, scheduleId, pairNum + 1, True)
    else:
        removeScheduleItemById_Current(currentScheduleStaged, scheduleId, pairNum + 1, False)
        addPairToFlatSchedule_Current(currentScheduleStaged, parameters, scheduleId, (scheduleDetailed1, scheduleDetailed2))

    schedule.CurrentSchedules[1] = json.loads(currentScheduleStaged.toJSON())
    schedule.save()

    schedulesAreSame = checkIfFlatScheduleDetailedEquals(currentScheduleMain, currentScheduleStaged)
    schedulesAreSame_Day = checkIfFlatScheduleDetailedEquals(changeSingleScheduleDay_Current(baseSchedule=currentScheduleMain, newSchedule=currentScheduleStaged, dateId=pk2), currentScheduleMain)
    if (schedulesAreSame and not schedulesAreSame_Day):
        raise AssertionError("Data mismatch: schedules are same, but not on a specific day (stageCurrentSchedulePair).")

    response = FlatScheduleResponse(None, currentScheduleStaged, schedulesAreSame, schedulesAreSame_Day)
    return Response(json.loads(response.toJSON()))

@api_view(['PUT'])
def applyBaseScheduleToCurrent(request, pk1, pk2, pk3):
    pk1 = int(pk1); pk2 = int(pk2); pk3 = int(pk3)

    schedule = getSavedSchedule()
    parameters = getDataFromDictGeneric(schedule.BaseParameters[0])
    baseScheduleMain = getDataFromDictGeneric(schedule.BaseSchedules[0])
    if getById(pk1, baseScheduleMain.nameList) == None:
        raise ValueError(f"Unknown name Id (applyBaseSchedule): {pk1}.")
    if not pk2 in range(8):
        raise ValueError(f"Wrong day Id (applyBaseSchedule): {pk2}.")
    if getById(pk3, parameters.dayList) == None:
        raise ValueError(f"Unknown date Id (applyBaseSchedule): {pk3}.")

    currentScheduleMain = getDataFromDictGeneric(schedule.CurrentSchedules[0])
    currentScheduleStaged = getDataFromDictGeneric(schedule.CurrentSchedules[1])
    applyBaseScheduleByNameAndDate(currentScheduleStaged, pk3, baseScheduleMain, pk1, pk2)

    schedule.CurrentSchedules[1] = json.loads(currentScheduleStaged.toJSON())
    schedule.save()

    schedulesAreSame = checkIfFlatScheduleDetailedEquals(currentScheduleMain, currentScheduleStaged)
    schedulesAreSame_Day = checkIfFlatScheduleDetailedEquals(changeSingleScheduleDay_Current(baseSchedule=currentScheduleMain, newSchedule=currentScheduleStaged, dateId=pk3), currentScheduleMain)
    if (schedulesAreSame and not schedulesAreSame_Day):
        raise AssertionError("Data mismatch: schedules are same, but not on a specific day (applyBaseScheduleToCurrent).")

    response = FlatScheduleResponse(None, currentScheduleStaged, schedulesAreSame, schedulesAreSame_Day)
    return Response(json.loads(response.toJSON()))

@api_view(['PUT'])
def stageBaseSchedulePair(request, pk1, pk2, pk3):
    pk1 = int(pk1); pk2 = int(pk2); pk3 = int(pk3)

    data = request.data
    if 'first' in data:
        scheduleDetailed1 = getDataFromDictGeneric(data['first'])
    else:
        scheduleDetailed1 = ScheduleDetailed()
    if 'second' in data:
        scheduleDetailed2 = getDataFromDictGeneric(data['second'])
    else:
        scheduleDetailed2 = ScheduleDetailed()

    if (checkScheduleDetailedValidity(scheduleDetailed1) == False or checkScheduleDetailedValidity(scheduleDetailed2) == False):
        raise ValueError(f"Supplied with incorrect data (uploadCurrentSchedulePair): {data}.")
    elif scheduleDetailed1.lessonNum == None or scheduleDetailed2.lessonNum == None:
        raise ValueError(f"Supplied with no lesson number (uploadCurrentSchedulePair): {data}.")
    elif abs(scheduleDetailed1.lessonNum - scheduleDetailed2.lessonNum) != 1 or int((scheduleDetailed1.lessonNum - 1) / 2) != int((scheduleDetailed2.lessonNum - 1) / 2):
        raise ValueError(f"Supplied with sub-pairs from different pairs (uploadCurrentSchedulePair): {data}.")

    if checkScheduleDetailedValidity(scheduleDetailed1) == None:
        scheduleDetailed1 = ScheduleDetailed(scheduleDetailed1.lessonNum)
    if checkScheduleDetailedValidity(scheduleDetailed2) == None:
        scheduleDetailed2 = ScheduleDetailed(scheduleDetailed2.lessonNum)
    pairNum = int(scheduleDetailed1.lessonNum / 2)

    schedule = getSavedSchedule()
    parameters = getDataFromDictGeneric(schedule.BaseParameters[0])

    if getById(pk1, parameters.groupList) == None:
        raise ValueError(f"Unknown group Id (uploadBaseSchedulePair): {pk1}.")
    if getById(pk2, parameters.dayList) == None:
        raise ValueError(f"Unknown day number (uploadBaseSchedulePair): {pk2}.")
    if not pairNum in range(APP_PAIR_MAX_AMOUNT):
        raise ValueError(f"Wrong pair number (uploadBaseSchedulePair): {pairNum}.")

    baseScheduleMain = getDataFromDictGeneric(schedule.BaseSchedules[0])
    baseScheduleStaged = getDataFromDictGeneric(schedule.BaseSchedules[1])

    if getById(pk3, baseScheduleStaged.nameList) == None:
        raise ValueError(f"Unknown base schedule name Id (uploadBaseSchedulePair): {pk3}.")

    if getById_Array(pk2, baseScheduleStaged.scheduleDay) is None:
        baseScheduleStaged.scheduleDay.append(Data_IntArray(pk2, []))
    if getById_Array(pk1, baseScheduleStaged.scheduleGroup) is None:
        baseScheduleStaged.scheduleGroup.append(Data_IntArray(pk1, []))
    if getById_Array(pk3, baseScheduleStaged.scheduleName) is None:
        baseScheduleStaged.scheduleName.append(Data_IntArray(pk3, []))

    scheduleId = getScheduleIdByGroupDateAndBaseScheduleId(baseScheduleStaged, pk2, pk1, pk3)
    chosenScheduleIdIsNew = (scheduleId is None)

    if chosenScheduleIdIsNew:
        scheduleId = getScheduleIdByGroupDateAndBaseScheduleId(baseScheduleMain, pk2, pk1, pk3)
        if scheduleId is None:
            scheduleId = getEmptyId(collectAllBaseScheduleIds())
        day_schedule_array = getById_Array(pk2, baseScheduleStaged.scheduleDay)
        group_schedule_array = getById_Array(pk1, baseScheduleStaged.scheduleGroup)
        name_schedule_array = getById_Array(pk3, baseScheduleStaged.scheduleName)

        day_schedule_array.scheduleId.append(scheduleId)
        group_schedule_array.scheduleId.append(scheduleId)
        name_schedule_array.scheduleId.append(scheduleId)

    if checkScheduleDetailedValidity(scheduleDetailed1) == None and checkScheduleDetailedValidity(scheduleDetailed2) == None:
        removeScheduleItemById_Base(baseScheduleStaged, scheduleId, pairNum + 1, True)
    else:
        removeScheduleItemById_Base(baseScheduleStaged, scheduleId, pairNum + 1, False)
        addPairToFlatSchedule_Base(baseScheduleStaged, parameters, scheduleId, (scheduleDetailed1, scheduleDetailed2))

    schedule.BaseSchedules[1] = json.loads(baseScheduleStaged.toJSON())
    schedule.save()

    schedulesAreSame = checkIfFlatScheduleBaseEquals(baseScheduleMain, baseScheduleStaged, True)
    schedulesAreSame_Day = checkIfFlatScheduleBaseEquals(changeSingleScheduleDay_Base(baseSchedule=baseScheduleMain, newSchedule=baseScheduleStaged, dateId=pk2, nameId=pk3), baseScheduleMain, False)
    if (schedulesAreSame and not schedulesAreSame_Day):
        raise AssertionError("Data mismatch: schedules are same, but not on a specific day (stageBaseSchedulePair).")

    response = FlatScheduleResponse(None, baseScheduleStaged, schedulesAreSame, schedulesAreSame_Day)
    return Response(json.loads(response.toJSON()))

@api_view(['PUT'])
def stageBaseScheduleName(request):
    data = request.data

    if not 'id' in data:
        id = None
    else:
        id = data['id']
    if not 'title' in data:
        name = None
    else:
        name = data['title']
    checkSum = 1 * int(not (id is None or id == -1)) + 2 * int(not (name is None or name == ""))

    schedule = getSavedSchedule()
    baseScheduleMain = getDataFromDictGeneric(schedule.BaseSchedules[0])
    baseScheduleStaged = getDataFromDictGeneric(schedule.BaseSchedules[1])

    if not (name is None or name == ""):
        for item in baseScheduleStaged.nameList:
            if item.title == name:
                raise ValueError(f"Schedule name already exists (stageBaseScheduleName): {data}.")

    match checkSum:
        case 0:
            new_id = getPossibleId_String(baseScheduleStaged.nameList)
            new_title_number = new_id
            new_title = f"Базовое расписание {new_title_number}"

            names_list = []
            for item in baseScheduleStaged.nameList:
                names_list.append(item.title)

            while new_title in names_list:
                new_title_number += 1
                new_title = f"Базовое расписание {new_title_number}"
            baseScheduleStaged.nameList.append(Data_IntString(new_id, new_title))
        case 1:
            ids_array = []
            name_id_array = getById_Array(id, baseScheduleStaged.scheduleName)
            if name_id_array is not None:
                ids_array.extend(name_id_array.scheduleId)
                for idToRemove in ids_array:
                    removeScheduleItemById_Base(baseScheduleStaged, idToRemove)
            if getById(id, baseScheduleStaged.nameList) is not None:
                baseScheduleStaged.nameList.remove(getById(id, baseScheduleStaged.nameList))
        case 2:
            new_id = getPossibleId_String(baseScheduleStaged.nameList)
            baseScheduleStaged.nameList.append(Data_IntString(new_id, name))
        case 3:
            if getById(id, baseScheduleStaged.nameList) == None:
                raise ValueError(f"Wrong schedule name id was supplied (stageBaseScheduleName): {id}.")
            getById(id, baseScheduleStaged.nameList).title = name

    schedule.BaseSchedules[1] = json.loads(baseScheduleStaged.toJSON())
    schedule.save()

    schedulesAreSame = checkIfFlatScheduleBaseEquals(baseScheduleMain, baseScheduleStaged, True)
    response = FlatScheduleResponse(None, baseScheduleStaged, schedulesAreSame, None)
    return Response(json.loads(response.toJSON()))

@api_view(['PUT'])
def applyCurrentScheduleChanges(request, pk1, pk2):
    pk1 = int(pk1); pk2 = int(pk2)

    schedule = getSavedSchedule()
    currentScheduleMain = getDataFromDictGeneric(schedule.CurrentSchedules[0])
    currentScheduleStaged = getDataFromDictGeneric(schedule.CurrentSchedules[1])

    if pk1 == -1:
        oldVersion = schedule.CurrentSchedules[0]['version']
        schedule.CurrentSchedules[0] = schedule.CurrentSchedules[1]
        schedule.CurrentSchedules[0]['version'] = oldVersion
        currentScheduleMain = currentScheduleStaged
        currentScheduleMain.version = oldVersion
        schedulesAreSame = True
    else:
        currentScheduleMain = changeSingleScheduleDay_Current(baseSchedule=currentScheduleMain, newSchedule=currentScheduleStaged, dateId=pk1)
        schedule.CurrentSchedules[0] = json.loads(currentScheduleMain.toJSON())
        schedulesAreSame = checkIfFlatScheduleDetailedEquals(currentScheduleMain, currentScheduleStaged)

    if pk2 != 0:
        curTime = round(time.time())
        schedule.CurrentSchedules[0]['version'] = curTime
        currentScheduleMain.version = curTime
    schedule.save()

    if pk1 != -1:
        if checkIfFlatScheduleDetailedEquals(changeSingleScheduleDay_Current(baseSchedule=currentScheduleMain, newSchedule=currentScheduleStaged, dateId=pk1), currentScheduleMain) != True:
            raise AssertionError("Results mismatch: the staged and main schedules aren't equal on the chosen day (applyCurrentScheduleChanges).")

    response = FlatScheduleResponse(currentScheduleMain, None, schedulesAreSame, True)
    return Response(json.loads(response.toJSON()))

@api_view(['PUT'])
def applyBaseScheduleChanges(request, pk1, pk2):
    pk1 = int(pk1); pk2 = int(pk2)

    schedule = getSavedSchedule()
    baseScheduleMain = getDataFromDictGeneric(schedule.BaseSchedules[0])
    baseScheduleStaged = getDataFromDictGeneric(schedule.BaseSchedules[1])

    if pk1 == -1 or pk2 == -1:
        schedule.BaseSchedules[0] = schedule.BaseSchedules[1]
        baseScheduleMain = baseScheduleStaged
        schedulesAreSame = True
    else:
        baseScheduleMain = changeSingleScheduleDay_Base(baseSchedule=baseScheduleMain, newSchedule=baseScheduleStaged, dateId=pk1, nameId=pk2)
        schedule.BaseSchedules[0] = json.loads(baseScheduleMain.toJSON())
        schedulesAreSame = checkIfFlatScheduleBaseEquals(baseScheduleMain, baseScheduleStaged, True)
    schedule.save()

    if pk1 != -1 or pk2 != -1:
        if checkIfFlatScheduleBaseEquals(changeSingleScheduleDay_Base(baseSchedule=baseScheduleMain, newSchedule=baseScheduleStaged, dateId=pk1, nameId=pk2), baseScheduleMain, False) != True:
            raise AssertionError("Results mismatch: the staged and main schedules aren't equal on the chosen day (applyBaseScheduleChanges).")

    response = FlatScheduleResponse(baseScheduleMain, None, schedulesAreSame, True)
    return Response(json.loads(response.toJSON()))

@api_view(['PUT'])
def resetCurrentScheduleChanges(request, pk):
    pk = int(pk)

    schedule = getSavedSchedule()
    currentScheduleMain = getDataFromDictGeneric(schedule.CurrentSchedules[0])
    currentScheduleStaged = getDataFromDictGeneric(schedule.CurrentSchedules[1])

    if pk == -1:
        oldVersion = schedule.CurrentSchedules[1]['version']
        schedule.CurrentSchedules[1] = schedule.CurrentSchedules[0]
        schedule.CurrentSchedules[1]['version'] = oldVersion
        currentScheduleStaged = currentScheduleMain
        currentScheduleStaged.version = oldVersion
        schedulesAreSame = True
    else:
        currentScheduleStaged = changeSingleScheduleDay_Current(baseSchedule=currentScheduleStaged, newSchedule=currentScheduleMain, dateId=pk)
        schedule.CurrentSchedules[1] = json.loads(currentScheduleStaged.toJSON())
        schedulesAreSame = checkIfFlatScheduleDetailedEquals(currentScheduleStaged, currentScheduleMain)
    schedule.save()

    if pk != -1:
        if checkIfFlatScheduleDetailedEquals(changeSingleScheduleDay_Current(baseSchedule=currentScheduleMain, newSchedule=currentScheduleStaged, dateId=pk), currentScheduleMain) != True:
            raise AssertionError("Results mismatch: the staged and main schedules aren't equal on the chosen day (applyCurrentScheduleChanges).")

    response = FlatScheduleResponse(None, currentScheduleStaged, schedulesAreSame, True)
    return Response(json.loads(response.toJSON()))

@api_view(['PUT'])
def resetBaseScheduleChanges(request, pk1, pk2):
    pk1 = int(pk1); pk2 = int(pk2)

    schedule = getSavedSchedule()
    baseScheduleMain = getDataFromDictGeneric(schedule.BaseSchedules[0])
    baseScheduleStaged = getDataFromDictGeneric(schedule.BaseSchedules[1])

    if pk1 == -1 or pk2 == -1:
        schedule.BaseSchedules[1] = schedule.BaseSchedules[0]
        baseScheduleStaged = baseScheduleMain
        schedulesAreSame = True
    else:
        baseScheduleStaged = changeSingleScheduleDay_Base(baseSchedule=baseScheduleStaged, newSchedule=baseScheduleMain, dateId=pk1, nameId=pk2)
        schedule.BaseSchedules[1] = json.loads(baseScheduleStaged.toJSON())
        schedulesAreSame = checkIfFlatScheduleBaseEquals(baseScheduleStaged, baseScheduleMain, True)
    schedule.save()

    if pk1 != -1 or pk2 != -1:
        if checkIfFlatScheduleBaseEquals(changeSingleScheduleDay_Base(baseSchedule=baseScheduleMain, newSchedule=baseScheduleStaged, dateId=pk1, nameId=pk2), baseScheduleMain, False) != True:
            raise AssertionError("Results mismatch: the staged and main schedules aren't equal on the chosen day (applyBaseScheduleChanges).")

    response = FlatScheduleResponse(None, baseScheduleStaged, schedulesAreSame, True)
    return Response(json.loads(response.toJSON()))


# Test FlatSchedule creation
if len(Model_FlatSchedule.objects.all()) == 0:
    flatScheduleParametersData = FlatScheduleParameters(cabinetList = [], groupList = [], lessonList = [], teacherList = [], dayList = [])
    flatScheduleDetailedData = FlatScheduleDetailed(scheduleDay = [], scheduleGroup = [], scheduleLesson = [], teacherLesson = [], cabinetLesson = [], version = 0)
    flatScheduleBaseData = FlatScheduleBase(nameList = [], scheduleName = [], scheduleDay = [], scheduleGroup = [], scheduleLesson = [], teacherLesson = [], cabinetLesson = [])
    flatScheduleParametersData._id = 0; flatScheduleDetailedData._id = 0; flatScheduleBaseData._id = 0
    flatScheduleBaseDataStaged = copy.copy(flatScheduleBaseData)
    flatScheduleDetailedDataStaged = copy.copy(flatScheduleDetailedData)
    flatScheduleDetailedDataStaged._id = 1; flatScheduleBaseDataStaged._id = 1
    flatSchedule = Model_FlatSchedule(_id=0, BaseSchedules = [json.loads(flatScheduleBaseData.toJSON()), json.loads(flatScheduleBaseDataStaged.toJSON())], CurrentSchedules = [json.loads(flatScheduleDetailedData.toJSON()), json.loads(flatScheduleDetailedDataStaged.toJSON())], BaseParameters = [json.loads(flatScheduleParametersData.toJSON())])

    flatSchedule.save()
updateDayList()