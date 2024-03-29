from pydash import objects, arrays, collections
from utils import DataUtils, LogTools
import json

sysLog = LogTools.SysLogs()


def getTagsFromPath(path):
    wayKey = ['get', 'post', 'patch', 'put', 'delete']

    for key in wayKey:
        if objects.get(path, key) != None:
            return path[key]['tags'][0]
    return None


def buildTop(data):
    '''
    构建swagger顶层目录结构
    :param data: swagger原始返回的信息
    :return:返回顶层元组信息
    '''
    try:
        dataObj = json.loads(data)
        tags = objects.get(dataObj, 'tags', [])
        tops = arrays.compact(tags)
        tops = arrays.mapcat(tops, lambda item: objects.assign(objects.clone(item), {'child': []}))

        return tops;
    except:
        sysLog.warn('JSON处理失败，请确认地址是否正确')
        return []


def buildChild(data, tags):
    '''
    构建child接口组
    :param data: 原始数据
    :param tasg: buildTop构建的tags组
    :return: 带有child信息的tags组
    '''
    try:

        dataObj = json.loads(data)
        tagsObj = objects.clone_deep(tags)

        # 遍历 tags ,嵌套遍历paths将对应的连接挂在到tags下的child中
        paths = objects.get(dataObj, 'paths')
        for tag in tagsObj:
            for path in paths:
                if tag['name'] == getTagsFromPath(paths[path]):
                    childItem = objects.clone_deep(paths[path])
                    tag['child'].append(objects.assign(childItem, {'path': path}))

        return tagsObj
    except:
        sysLog.warn('JSON处理失败，请确认地址是否正确')
        return []


def getInterfaceCount(tags):
    rowIndex = 0
    for row in range(len(tags)):
        for childIndex in range(len(tags[row]['child'])):
            rowData = tags[row]['child'][childIndex]
            methodTypes = DataUtils.getValidMethod(rowData)
            rowIndex += len(methodTypes)
    return rowIndex


def buildListData(tags, keyWord=''):
    listData = []

    for row in range(len(tags)):
        for childIndex in range(len(tags[row]['child'])):
            rowData = tags[row]['child'][childIndex]

            path = rowData['path']
            methodTypes = DataUtils.getValidMethod(rowData)

            for methodType in methodTypes:
                itemData = objects.clone_deep(tags[row]['child'][childIndex][methodType])
                itemData = objects.assign(itemData, {'path': path, 'type': methodType})
                listData.append(itemData)

    return listData


def _filterCallBack(item, keyWord):
    keys = ['summary', 'path', 'type']

    # tags 为数组结构 单独处理
    if objects.get(item, 'tags')[0].find(keyWord) >= 0:
        return True

    for key in keys:
        if objects.get(item, key).find(keyWord) >= 0:
            return True

    return False


def filter(listData, keyWord):
    return collections.filter_(listData, lambda item: _filterCallBack(item, keyWord))


def buildFields(apiItem, data):
    ref = objects.get(apiItem, 'responses.200.schema.$ref')

    if ref is None:
        ref = objects.get(apiItem, 'responses.200.schema.items.$ref')

    ref = ref.replace('#/definitions/', '')

    dataObj = json.loads(data)
    tempRef = objects.get(dataObj, 'definitions.' + ref + '.properties.data.items.$ref')

    if tempRef:
        ref = tempRef

    try:
        cols = []
        if tempRef is None:
            cols = objects.get(dataObj, 'definitions.' + ref + '.properties')
        else:
            ref = ref.replace('#/definitions/', '')
            cols = objects.get(dataObj, 'definitions.' + ref + '.properties')

        fields = []
        for key in cols:
            fields.append({'key': key, 'name': cols[key]})
        return fields
    except:
        return []
# responses => 200 => schema => $ref

# definitions => #/definitions/PageResult«合同付款-管理列表-修改» => properties => data => items

#         #/definitions => 合同付款-管理列表-修改 => properties

#   遍历key，val为 {"type": "number",
#           "description": "合同金额 - 合同的总执行金额"}
