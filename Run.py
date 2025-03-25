import pytest,time
import os

if __name__ == '__main__':
    # 切换工作目录到脚本所在目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 确保Report目录存在
    report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Report')
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
    
    # 提示用户选择下载源
    print("请选择小说下载源：")
    print("1. 万书屋")
    print("2. 辣文小说18+（男生视角）")
    
    选择 = input("请输入选择的序号：")
    
    # 生成报告文件名
    report_file = os.path.join('Report', f'report_{time.strftime("%Y_%m_%d_%H_%M_%S")}.html')
    
    if 选择 == "1":
        pytest.main(['-s','-v', './TestCase/万书屋.py',
                    f'--html=./{report_file}','--self-contained-html'])
    elif 选择 == "2":
        pytest.main(['-s','-v', './TestCase/辣文小说18+.py',
                    f'--html=./{report_file}','--self-contained-html'])
    else:
        print("无效选择，程序已退出")
    


    


    