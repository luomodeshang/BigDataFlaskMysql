from main_yield import Output_normalize_PLC_single_workpiece
from datetime import datetime, timedelta
from Model_Computer import *
# 获取当前时间并格式化为指定格式

def Get_TheClose_Item():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    now = datetime.now()
    one_hour_ago = now - timedelta(hours=0.5)
    formatted_time = one_hour_ago.strftime("%Y-%m-%d %H:%M:%S")
    # print(formatted_time,current_time)
    Clost_Item=Output_normalize_PLC_single_workpiece(formatted_time,current_time)[-1]
    return Clost_Item

print("2025年12月4日：",Get_TheClose_Item()[-4:-1])


def convert_to_sample_input(data_list):                                                                              
    # 将所有数值转换为字符串并用空格连接
    return ' '.join(map(str, data_list))

def classify_err_type():
    original_list=Get_TheClose_Item()
    sample_input = convert_to_sample_input(original_list)
    result = predict_sample(sample_input, model, scaler, class_mapping, device)
    print("获取最新数据分类结果")
    return result,original_list

# print(classify_err_type())