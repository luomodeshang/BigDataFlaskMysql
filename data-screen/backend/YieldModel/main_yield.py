# 包含单工件 多工件
# 但是一次只能分析一组数据
# 即PLC机械臂完成 1.1-1.4  (2.1-2.7)*n 2.8

from configparser import ConfigParser
from collections import Counter
from datetime import datetime, timedelta
import pandas as pd
import pymysql

class Config:
    def __init__(self):
        self.X_scan_postion1 = 135
        self.X_scan_postion2 = 270
        self.X_scan_postion3 = 135
        self.X_scan_postion4 = 270

        self.Y_scan_postion1 = 118
        self.Y_scan_postion2 = 118
        self.Y_scan_postion3 = 23
        self.Y_scan_postion4 = 23

def init_database_index():
    columns = [
        "Speed_X",  # 0
        "Speed_Y",  # 1
        "Speed_Z",  # 2
        "Speed_R",  # 3
        "positioing_error_X",  # 4
        "positioing_error_Y",  # 5
        "acceleration_X",  # 6
        "acceleration_Y",  # 7
        "acceleration_Z",  # 8
        "acceleration_R",  # 9
        "visual_error_X",  # 10
        "visual_error_Y",  # 11
        "fit_error_X",  # 12
        "fit_error_Y",  # 13
        "vibration_X",  # 14
        "vibration_Z",  # 15
        "noise_X",  # 16
        "PLC_step",  # 17
        "absolute_position_X",  # 18
        "absolute_position_Y",  # 19
        "offset_X",  # 20
        "offset_Y",  # 21
        "offset_R",  # 22
        "Grating_feedback_X",  # 23
        "Grating_feedback_Y",  # 24
        "setting_red_circle_X",  # 25
        "setting_red_circle_Y",  # 26
        "setting_blue_circle_X",  # 27
        "setting_blue_circle_Y",  # 28
        "setting_yellow_square_X",  # 29
        "setting_yellow_square_Y",  # 30
        "setting_blue_square_X",  # 31
        "setting_blue_square_Y",  # 32
        "visual_scanning_pixel_coordinate_X",  # 33
        "visual_scanning_pixel_coordinate_Y",  # 34
        "visual_setting_pixel_coordinate_X",  # 35
        "visual_setting_pixel_coordinate_Y",  # 36
        "visual_scanning_world_coordinate_X",  # 37
        "visual_scanning_world_coordinate_Y"  # 38
    ]
    return columns

def get_naZero_data(List,Column_item,top,bottom):
    # 找到二位列表中 固定列 某一行段中非零值
    for i in range(bottom-top+1):
        if List[i+top][Column_item] != 0:
            return List[i+top][Column_item]
    return -1

def Get_NaZero_data_From_especific_PLC_step(List,Column_item,PLC_step):
    # 从分割好的单个工件步骤List里
    # 获取对应的PLC_step范围内首个非零值
    for i in range(len(List)):
        if List[i][17] == PLC_step and List[i][Column_item] != 0:
            return List[i][Column_item]
    return -1

def get_Most_data(List):
    if not List:
        return None
    count = Counter(List)
    max_count = max(count.values())
    modes = [num for num, cnt in count.items() if cnt == max_count]
    return modes if len(modes) > 1 else modes[0]


def init_hash_for_PLC_step():
    # 为每个工件建立哈希表,存储完整的PLC步骤
    PLC_SETP_LEN = 12
    Hash_List_for_PLC = []
    for i in range(PLC_SETP_LEN):
        Hash_List_for_PLC.append([])
    return Hash_List_for_PLC


def Connect_SQL(begin_time,end_time):
    # 从数据库取数据时 只限制第一次流程 详见第一行注释
    config = ConfigParser()
    config.read('新建文本文档.ini')
    host = config.get('DEFAULT', 'Host')  # MySQL主机地址
    port = config.getint('DEFAULT', 'Port')  # MySQL端口
    database = config.get('DEFAULT', 'Database')  # 数据库名称
    user = config.get('DEFAULT', 'User')  # 用户名
    password = config.get('DEFAULT', 'Password')  # 密码

    try:
        # 连接到MySQL数据库
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4'
        )
        # 创建游标
        cursor = conn.cursor()
        sql = '''SELECT 
                      Speed_X,
                      Speed_Y,
                      Speed_Z,
                      Speed_R,
                      positioing_error_X,
                      positioing_error_Y,
                      acceleration_X,
                      acceleration_Y,
                      acceleration_Z,
                      acceleration_R,
                      visual_error_X,
                      visual_error_Y,
                      fit_error_X,
                      fit_error_Y,
                      vibration_X,
                      vibration_Z,
                      noise_X,
                      PLC_step,
                      absolute_position_X,
                      absolute_position_Y,
                      offset_X,
                      offset_Y,
                      offset_R,
                      Grating_feedback_X,
                      Grating_feedback_Y,
                      setting_red_circle_X,
                      setting_red_circle_Y,
                      setting_blue_circle_X,
                      setting_blue_circle_Y,
                      setting_yellow_square_X,
                      setting_yellow_square_Y,
                      setting_blue_square_X,
                      setting_blue_square_Y,
                      visual_scanning_pixel_coordinate_X,
                      visual_scanning_pixel_coordinate_Y,
                      visual_setting_pixel_coordinate_X,
                      visual_setting_pixel_coordinate_Y,
                      visual_scanning_world_coordinate_X,
                      visual_scanning_world_coordinate_Y,
                      creation_date
                  FROM BK_DataModel'''

        # 添加时间范围条件
        params = []
        if begin_time and end_time:
            sql += " WHERE creation_date BETWEEN %s AND %s"
            params.extend([begin_time, end_time])

        # 最后添加排序
        sql += " ORDER BY creation_date ASC"

        # 执行查询
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)

        rows = cursor.fetchall()
        conn.close()
        return rows

    except pymysql.Error as e:
        print(f"Error connecting to MySQL: {type(e)} {e}")
        return None

    # 只截获第一段非零数据流
    Final_result = []
    Flag_na_Zeor=-1
    Last_PLC_step=-1
    for item in result:
        if Last_PLC_step != 0.0 and item[17] == 0.0:
            Flag_na_Zeor += 1
        if Flag_na_Zeor!=-1:
            if Flag_na_Zeor == 1:
                break
            Last_PLC_step = item[17]
            if item[17] != 0.0:
                Final_result.append(item)
    return  Final_result


Yield_columns=['all定位误差X-1', 'all定位误差Y-1', 'all定位误差X-2', 'all定位误差Y-2',
                               'all定位误差X-3', 'all定位误差Y-3', 'all定位误差X-4', 'all定位误差Y-4',
                               'all物件坐标X-1', 'all物件坐标Y-1', 'all物理坐标X-1', 'all物理坐标Y-1',

                               'catch定位误差X(移动到拍照位)', 'catch定位误差Y(移动到拍照位)',
                               'catch光栅反馈X(移动到拍照位)', 'catch光栅反馈Y(移动到拍照位)',
                               '视觉误差X', '视觉误差Y',
                               'catch复拍物件坐标X', 'catch复拍物件坐标Y', 'catch复拍物理坐标X', 'catch复拍物理坐标Y',
                               'catchPLC坐标X', 'catchPLC坐标Y',
                               'catch定位误差X', 'catch定位误差Y',
                               'catch光栅反馈X', 'catch光栅反馈Y',
                               'releasePLC坐标X', 'releasePLC坐标Y', 'release定位误差X', 'release定位误差Y',
                               'release光栅反馈X', 'release光栅反馈Y', '贴合误差X', '贴合误差Y',
                               'release视觉坐标X(像素)', 'release视觉坐标Y(像素)'
                               ]

Yield_index = {
    'all定位误差X-1': 0,
    'all定位误差Y-1': 1,
    'all定位误差X-2': 2,
    'all定位误差Y-2': 3,
    'all定位误差X-3': 4,
    'all定位误差Y-3': 5,
    'all定位误差X-4': 6,
    'all定位误差Y-4': 7,
    'all物件坐标X-1': 8,
    'all物件坐标Y-1': 9,
    'all物理坐标X-1': 10,
    'all物理坐标Y-1': 11,
    'catch定位误差X(移动到拍照位)': 12,
    'catch定位误差Y(移动到拍照位)': 13,
    'catch光栅反馈X(移动到拍照位)': 14,
    'catch光栅反馈Y(移动到拍照位)': 15,
    '视觉误差X': 16,
    '视觉误差Y': 17,
    'catch复拍物件坐标X': 18,
    'catch复拍物件坐标Y': 19,
    'catch复拍物理坐标X': 20,
    'catch复拍物理坐标Y': 21,
    'catchPLC坐标X': 22,
    'catchPLC坐标Y': 23,
    'catch定位误差X': 24,
    'catch定位误差Y': 25,
    'catch光栅反馈X': 26,
    'catch光栅反馈Y': 27,
    'releasePLC坐标X': 28,
    'releasePLC坐标Y': 29,
    'release定位误差X': 30,
    'release定位误差Y': 31,
    'release光栅反馈X': 32,
    'release光栅反馈Y': 33,
    '贴合误差X': 34,
    '贴合误差Y': 35,
    'release视觉坐标X(像素)': 36,
    'release视觉坐标Y(像素)': 37
}

def Cut_data_to_Single_workpiece(Origin_data):
    Origin_Result=[]
    Single_work_PLC = []
    PLC_Step=17
    write_Flag=False
    Last_PCL_Step=-1
    for item_data in Origin_data:
        # 由于部分信息存在滞后性 最后的2.7应该补充一个下一个工件2.1的信息
        # 直到下一个工件的fit error有效 才停止写入
        if (item_data[PLC_Step]==2.1 or item_data[PLC_Step]==2.2 ) and write_Flag==False:
            # 首次到这个开始点 并且 此时不属于写入段
            write_Flag=True
            # 开始写入
            Single_work_PLC.append(item_data)
        if (item_data[12]!=0 or item_data[13]!=0 ) and write_Flag==True:
            # 2025年7月16日补丁，XY两个误差有一个不为零即认为是终点
            # 找到这个结束点 停止写入
            write_Flag=False
            # 停止写入
            Single_work_PLC.append(item_data)
            Origin_Result.append(Single_work_PLC)
            Single_work_PLC=[]
            Single_work_PLC.append(item_data)
        if write_Flag==True:
            # 正常写入
            Single_work_PLC.append(item_data)
        Last_PCL_Step=item_data[PLC_Step]
    return Origin_Result

def index_area_For_1_4(Origin_data):
    # 定位初始拍照索引
    result=[-1,-1,-1,-1,-1]
    for index in range(len(Origin_data)):
        if Origin_data[index][17]==1.1 and result[0]==-1:
            result[0]=index
        if Origin_data[index][17]==1.2 and result[1]==-1:
            result[1]=index
        if Origin_data[index][17]==1.3 and result[2]==-1:
            result[2]=index
        if Origin_data[index][17]==1.4 and result[3]==-1:
            result[3]=index
        # 四号位要读取到2.1结尾
        if Origin_data[index][17]==2.1 and result[4]==-1:
            result[4]=index-1
    return  result

def Output_normalize_PLC_single_workpiece(begin_time_str, end_time_str):
    # 给单工件输出规范数据格式
    # 变量名与索引对应关系
    # 该数据格式仅适用于数据库数据
    begin_time = datetime.strptime(begin_time_str, '%Y-%m-%d %H:%M:%S')
    end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
    # print(begin_time, end_time)
    columns_mapping = {
        'Speed_X': 0,
        'Speed_Y': 1,
        'Speed_Z': 2,
        'Speed_R': 3,
        'positioing_error_X': 4,
        'positioing_error_Y': 5,
        'acceleration_X': 6,
        'acceleration_Y': 7,
        'acceleration_Z': 8,
        'acceleration_R': 9,
        'visual_error_X': 10,
        'visual_error_Y': 11,
        'fit_error_X': 12,
        'fit_error_Y': 13,
        'vibration_X': 14,
        'vibration_Z': 15,
        'noise_X': 16,
        'PLC_step': 17,
        'absolute_position_X': 18,
        'absolute_position_Y': 19,
        'offset_X': 20,
        'offset_Y': 21,
        'offset_R': 22,
        'Grating_feedback_X': 23,
        'Grating_feedback_Y': 24,
        'setting_red_circle_X': 25,
        'setting_red_circle_Y': 26,
        'setting_blue_circle_X': 27,
        'setting_blue_circle_Y': 28,
        'setting_yellow_square_X': 29,
        'setting_yellow_square_Y': 30,
        'setting_blue_square_X': 31,
        'setting_blue_square_Y': 32,
        'visual_scanning_pixel_coordinate_X': 33,
        'visual_scanning_pixel_coordinate_Y': 34,
        'visual_setting_pixel_coordinate_X': 35,
        'visual_setting_pixel_coordinate_Y': 36,
        'visual_scanning_world_coordinate_X': 37,
        'visual_scanning_world_coordinate_Y': 38,
        'creation_date': 39
    }
    Final_Result=[]
    Origin_Result=Connect_SQL(begin_time, end_time)


    # db_index=init_database_index()
    # 工件的步骤阶段切片 就是每个工件的2.1-2.7加上下个工件的2.1
    # print(Origin_Result)
    Single_data_List=Cut_data_to_Single_workpiece(Origin_Result)


    # 工件个数
    Lenth=len(Single_data_List)
    print("工件个数为：",Lenth)
    # for i in Single_data_List:
    #     print("========================")
    #     for j in i:
    #         print(j[17:])
    for i_num in range(Lenth):
        Final_Result.append([0]*38)


    # for item in Origin_Result:
    #     print(item[17])



    # 先处理all工件误差 该值由1.1-1.4 的定位误差计算得到 所有工件均适用
    # positioing_error_X positioing_error_Y 计算
    Last_PLC=0.0
    temp=[]
    for num in range(len(Origin_Result)):
        # print(Origin_Result[num][columns_mapping['PLC_step']],end=' ')
        # print(Origin_Result[num][columns_mapping['positioing_error_X']])
        # temp.append(Origin_Result[num][columns_mapping['positioing_error_X']])
        # temp.append(Origin_Result[num][columns_mapping['positioing_error_Y']])
        if Origin_Result[num][columns_mapping['PLC_step']]==1.1 and Last_PLC!=1.1:
            temp.append( Origin_Result[num][columns_mapping['positioing_error_X']])
            temp.append( Origin_Result[num][columns_mapping['positioing_error_Y']])
        if Origin_Result[num][columns_mapping['PLC_step']]==1.2 and Last_PLC!=1.2:
            temp.append( Origin_Result[num][columns_mapping['positioing_error_X']])
            temp.append( Origin_Result[num][columns_mapping['positioing_error_Y']])
        if Origin_Result[num][columns_mapping['PLC_step']]==1.3 and Last_PLC!=1.3:
            temp.append( Origin_Result[num][columns_mapping['positioing_error_X']])
            temp.append( Origin_Result[num][columns_mapping['positioing_error_Y']])
        if Origin_Result[num][columns_mapping['PLC_step']]==1.4 and Last_PLC!=1.4:
            temp.append( Origin_Result[num][columns_mapping['positioing_error_X']])
            temp.append( Origin_Result[num][columns_mapping['positioing_error_Y']])
        Last_PLC=Origin_Result[num][columns_mapping['PLC_step']]
    for index in range(Lenth):
        Final_Result[index][Yield_index['all定位误差X-1']] = temp[0]
        Final_Result[index][Yield_index['all定位误差Y-1']] = temp[1]
        Final_Result[index][Yield_index['all定位误差X-2']] = temp[2]
        Final_Result[index][Yield_index['all定位误差Y-2']] = temp[3]
        Final_Result[index][Yield_index['all定位误差X-3']] = temp[4]
        Final_Result[index][Yield_index['all定位误差Y-3']] = temp[5]
        Final_Result[index][Yield_index['all定位误差X-4']] = temp[6]
        Final_Result[index][Yield_index['all定位误差Y-4']] = temp[7]






    origin_photo_setting=index_area_For_1_4(Origin_Result)
    print("初始拍照位",origin_photo_setting)
    for index in range(0,4):
        # 为每个工件计算物件坐标 pixel和物理坐标 world
        # 包括四号位共五个点位 四个拍照段
        # 初版本设计每个象限内只放置一个工件
        # 输出仅为4行 因为数据库每次拍照只有一组样本值
        print(index,'号位置拍照位定位数据')
        Final_Result[index][Yield_index['all物件坐标X-1']]=get_naZero_data(Origin_Result,
                                                                           columns_mapping['visual_scanning_pixel_coordinate_X'],
                                                                           origin_photo_setting[index],
                                                                           origin_photo_setting[index+1])
        Final_Result[index][Yield_index['all物件坐标Y-1']] = get_naZero_data(Origin_Result,
                                                                             columns_mapping[
                                                                                 'visual_scanning_pixel_coordinate_Y'],
                                                                             origin_photo_setting[index],
                                                                             origin_photo_setting[index + 1])
        Final_Result[index][Yield_index['all物理坐标X-1']] = get_naZero_data(Origin_Result,
                                                                             columns_mapping[
                                                                                 'visual_scanning_world_coordinate_X'],
                                                                             origin_photo_setting[index],
                                                                             origin_photo_setting[index + 1])
        Final_Result[index][Yield_index['all物理坐标Y-1']] = get_naZero_data(Origin_Result,
                                                                             columns_mapping[
                                                                                 'visual_scanning_world_coordinate_Y'],
                                                                             origin_photo_setting[index],
                                                                             origin_photo_setting[index + 1])


    # catch定位误差和光栅反馈捕获时间为每个工件刚进入2.2时
    Last_PLC=0.0
    workpiece=-1
    for index in range(len(Origin_Result)):
        if Last_PLC==2.1 and Origin_Result[index][columns_mapping['PLC_step']]==2.2:
            workpiece+=1
            print("第", workpiece, "个工件")
            if(workpiece<len(Final_Result)):
                Final_Result[workpiece][Yield_index['catch定位误差X(移动到拍照位)']]=Origin_Result[index][columns_mapping['positioing_error_X']]
                Final_Result[workpiece][Yield_index['catch定位误差Y(移动到拍照位)']] = Origin_Result[index][columns_mapping['positioing_error_Y']]
                Final_Result[workpiece][Yield_index['catch光栅反馈X(移动到拍照位)']] = Origin_Result[index][columns_mapping['Grating_feedback_X']]
                Final_Result[workpiece][Yield_index['catch光栅反馈Y(移动到拍照位)']] = Origin_Result[index][columns_mapping['Grating_feedback_Y']]
        Last_PLC=Origin_Result[index][columns_mapping['PLC_step']]




    # 视觉误差 复拍物件坐标为当前工件2.2阶段不为零时，应采用分割后的工件的数据格式
    # Get_NaZero_data_From_especific_PLC_step这个获取
    # [单个工件的流程2.1-2.7] 里面对应column 的某个plcstep里面的
    # 第一个非零数据
    for index in range(len(Single_data_List)):
        Final_Result[index][Yield_index['视觉误差X']]=Get_NaZero_data_From_especific_PLC_step(Single_data_List[index],
                                                                                              columns_mapping["visual_error_X"],2.2)
        Final_Result[index][Yield_index['视觉误差Y']] = Get_NaZero_data_From_especific_PLC_step(Single_data_List[index],
                                                                                              columns_mapping["visual_error_Y"],2.2)
        Final_Result[index][Yield_index['catch复拍物件坐标X']] = Get_NaZero_data_From_especific_PLC_step(Single_data_List[index],
                                                                                                columns_mapping["visual_scanning_pixel_coordinate_X"],2.2)
        Final_Result[index][Yield_index['catch复拍物件坐标Y']] = Get_NaZero_data_From_especific_PLC_step(Single_data_List[index],
                                                                                                columns_mapping["visual_scanning_pixel_coordinate_Y"],2.2)
        Final_Result[index][Yield_index['catch复拍物理坐标X']] = Get_NaZero_data_From_especific_PLC_step(Single_data_List[index],
                                                                                                columns_mapping["visual_scanning_world_coordinate_X"],2.2)
        Final_Result[index][Yield_index['catch复拍物理坐标Y']] = Get_NaZero_data_From_especific_PLC_step(Single_data_List[index],
                                                                                                columns_mapping["visual_scanning_world_coordinate_Y"],2.2)

        Final_Result[index][Yield_index['catchPLC坐标X']] = Get_NaZero_data_From_especific_PLC_step(
            Single_data_List[index],
            columns_mapping["absolute_position_X"], 2.2)
        Final_Result[index][Yield_index['catchPLC坐标Y']] = Get_NaZero_data_From_especific_PLC_step(
            Single_data_List[index],
            columns_mapping["absolute_position_Y"], 2.2)

        Final_Result[index][Yield_index['catch光栅反馈X']] = Get_NaZero_data_From_especific_PLC_step(
            Single_data_List[index],
            columns_mapping["Grating_feedback_X"], 2.3)

        Final_Result[index][Yield_index['catch光栅反馈Y']] = Get_NaZero_data_From_especific_PLC_step(
            Single_data_List[index],
            columns_mapping["Grating_feedback_Y"], 2.3)

        Final_Result[index][Yield_index['catch定位误差X']] = Get_NaZero_data_From_especific_PLC_step(
            Single_data_List[index],
            columns_mapping["positioing_error_X"], 2.3)
        Final_Result[index][Yield_index['catch定位误差Y']] = Get_NaZero_data_From_especific_PLC_step(
            Single_data_List[index],
            columns_mapping["positioing_error_Y"], 2.3)

        Final_Result[index][Yield_index['releasePLC坐标X']] = Get_NaZero_data_From_especific_PLC_step(
            Single_data_List[index],
            columns_mapping["absolute_position_X"], 2.4)
        Final_Result[index][Yield_index['releasePLC坐标Y']] = Get_NaZero_data_From_especific_PLC_step(
            Single_data_List[index],
            columns_mapping["absolute_position_Y"], 2.4)


        Final_Result[index][Yield_index['release定位误差X']] = Get_NaZero_data_From_especific_PLC_step(
            Single_data_List[index],
            columns_mapping["positioing_error_X"], 2.5)
        Final_Result[index][Yield_index['release定位误差Y']] = Get_NaZero_data_From_especific_PLC_step(
            Single_data_List[index],
            columns_mapping["positioing_error_Y"], 2.5)

        Final_Result[index][Yield_index['release光栅反馈X']] = Get_NaZero_data_From_especific_PLC_step(
            Single_data_List[index],
            columns_mapping["Grating_feedback_X"], 2.5)
        Final_Result[index][Yield_index['release光栅反馈Y']] = Get_NaZero_data_From_especific_PLC_step(
            Single_data_List[index],
            columns_mapping["Grating_feedback_Y"], 2.5)

        Final_Result[index][Yield_index['贴合误差X']] = Single_data_List[index][-1][columns_mapping["fit_error_X"]]
        Final_Result[index][Yield_index['贴合误差Y']] = Single_data_List[index][-1][columns_mapping["fit_error_Y"]]

        Final_Result[index][Yield_index['release视觉坐标X(像素)']] = Single_data_List[index][-1][columns_mapping["visual_setting_pixel_coordinate_X"]]
        Final_Result[index][Yield_index['release视觉坐标Y(像素)']] = Single_data_List[index][-1][columns_mapping["visual_setting_pixel_coordinate_Y"]]

    return Final_Result



# current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
# now = datetime.now()
# one_hour_ago = now - timedelta(hours=0.5)
# formatted_time = one_hour_ago.strftime("%Y-%m-%d %H:%M:%S")
# res=Output_normalize_PLC_single_workpiece('2025-11-27 11:00:28','2026-09-05 14:10:37'
# )
# print(res[-1])






