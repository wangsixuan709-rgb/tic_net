# import csv
# import os
# import numpy as np
# from evaluationScript.tools import csvTools
# import nrrd
# import matplotlib.pyplot as plt
# import sys
# from config import data_config, train_config


# def generate_test_anno(anno_dir, test_list_dir, test_anno_dir):
#     """
#     generate the annotations csv file for the image which need to be visualized.
#     anno_dir: all annotations in one file
#     test_list_dir: ct filename list
#     test_anno_dir: output to a csv file
#     """
#     test_list = csvTools.readCSV(test_list_dir)
#     anno_list = csvTools.readCSV(anno_dir)

#     test_id_list = []

#     for id in test_list:
#         test_id_list.append(id[0])

#     try:
#         with open(test_anno_dir, 'w') as csvfile:
#             writer = csv.writer(csvfile)
#             for anno in anno_list:
#                 if anno[0] in test_id_list:
#                     writer.writerow([anno[0], anno[1], anno[2], anno[3], anno[4]])

#     except:
#         print("Unexpected error:", sys.exc_info()[0])


# def f(data):
#     return float(data)


# def draw_nms(predicts_list, threshold):
#     pd_list = np.array(predicts_list, dtype=np.float32)

#     x1 = pd_list[:, 0] - pd_list[:, 3]
#     y1 = pd_list[:, 1] - pd_list[:, 3]
#     z1 = pd_list[:, 2] - pd_list[:, 3]
#     x2 = pd_list[:, 0] + pd_list[:, 3]
#     y2 = pd_list[:, 1] + pd_list[:, 3]
#     z2 = pd_list[:, 2] + pd_list[:, 3]
#     scores = pd_list[:, 4]

#     order = scores.argsort()[::-1]

#     areas = (x2 - x1 + 1) * (y2 - y1 + 1) * (z2 - z1 + 1)
#     keep = []

#     while order.size > 0:
#         i = order[0]
#         keep.append(i)
#         xx1 = np.maximum(x1[i], x1[order[1:]])
#         yy1 = np.maximum(y1[i], y1[order[1:]])
#         zz1 = np.maximum(z1[i], z1[order[1:]])
#         xx2 = np.minimum(x2[i], x2[order[1:]])
#         yy2 = np.minimum(y2[i], y2[order[1:]])
#         zz2 = np.maximum(z2[i], z2[order[1:]])
#         inter = np.maximum(0.0, xx2 - xx1 + 1) * np.maximum(0.0, yy2 - yy1 + 1) * np.maximum(0.0, zz2 - zz1 + 1)
#         iou_3d = inter / (areas[i] + areas[order[1:]] - inter)
#         inds = np.where(iou_3d <= threshold)[0]
#         order = order[inds + 1]
#     bbox = pd_list[keep]

#     return bbox.tolist()


# def draw_boxes(filename, pid, gt_list, pred_list, outpath):
#     arr, options = nrrd.read(filename)
#     png_dir = outpath + pid
#     if not os.path.exists(png_dir):
#         os.makedirs(png_dir)

#     txt_color = '#000000'
#     pred_color = '#FFFFFF'
#     gt_color = '#DC143C'

#     for i, slice in enumerate(arr):
#         plt.figure()
#         plt.xticks([])
#         plt.yticks([])
#         plt.axis('off')
#         plt.imshow(slice, cmap="bone")
#         # draw prediction
#         for axis in pred_list:

#             start = int(axis[2] - int(axis[3] / 2))
#             end = int(axis[2] + int(axis[3] / 2))
#             if start <= i <= end:
#                 rect = plt.Rectangle(
#                     (axis[0] - axis[3] / 2, axis[1] - axis[3] / 2),
#                     axis[3], axis[3],
#                     fill=False,
#                     edgecolor=pred_color,
#                     linewidth=2
#                 )
#                 plt.gca().add_patch(rect)
#                 plt.text(
#                     axis[0] - axis[3] / 2, axis[1] - axis[3] / 2,
#                     round(data[4], 2),
#                     color=txt_color,
#                     bbox={'edgecolor': pred_color, 'facecolor': pred_color, 'alpha': 0.5, 'pad': 0}
#                 )

#         # draw ground-truth
#         for data in gt_list:
#             start = int(data[2] - int(data[3] / 2))
#             end = int(data[2] + int(data[3] / 2))
#             if start <= i <= end:
#                 rect = plt.Rectangle(
#                     (data[0] - data[3] / 2, data[1] - data[3] / 2),
#                     data[3], data[3],
#                     fill=False,
#                     edgecolor=gt_color,
#                     linewidth=2
#                 )
#                 plt.gca().add_patch(rect)

#         plt.savefig(png_dir + "/{}.png".format(i))
#         plt.close()


# def draw_one_fold(n):
#     # new annos after preprocess
#     anno_dir = data_config['new_annos_dir']
#     # generate gt data via detection result
#     test_anno_dir = 'annotations/test_anno.csv'
#     # original img folder
#     preprocessed_path = data_config['preprocessed_data_dir']
#     # ct need to be visualized
#     val_path = "detection/example.csv"
#     out_path = "detection/"
#     # detection result data 
#     result_path = 'results/transformer_conv_fpr/{}_fold/res/100/FROC/submission_ensemble.csv'.format(n)

#     generate_test_anno(anno_dir, val_path, test_anno_dir)

#     pid_list = []
#     pid_data = csvTools.readCSV(val_path)
#     for i in pid_data:
#         pid_list.append(i[0])

#     gt_data = csvTools.readCSV(test_anno_dir)
#     pred_data = csvTools.readCSV(result_path)[1:]

#     for pid in pid_list:
#         gt_list = []
#         for i in gt_data:
#             if pid == i[0]:
#                 data = i[1:]
#                 gt_list.append(data)

#         for i in range(len(gt_list)):
#             for j in range(4):
#                 gt_list[i][j] = f(gt_list[i][j])

#         pred_list = []
#         for i in pred_data:
#             if pid == i[0]:
#                 data = i[1:]
#                 pred_list.append(data)

#         for i in range(len(pred_list)):
#             for j in range(5):
#                 pred_list[i][j] = f(pred_list[i][j])

#         pd_list = draw_nms(pred_list, 0.1)
#         filename = preprocessed_path + '/' + pid + ".nrrd"

#         draw_boxes(filename, pid, gt_list, pd_list, out_path)

#         print('-- Finished # {}'.format(filename))


# if __name__ == "__main__":
#     draw_one_fold(9)
import csv
import os
import numpy as np
from evaluationScript.tools import csvTools
import nrrd
import matplotlib.pyplot as plt
import sys
from config import data_config, train_config


def create_example_csv_if_needed(result_path, example_path, num_samples=5):
    """如果example.csv不存在，自动创建它"""
    if os.path.exists(example_path):
        print(f"example.csv已存在: {example_path}")
        return True
    
    print("example.csv不存在，正在自动创建...")
    
    if not os.path.exists(result_path):
        print(f"错误：检测结果文件不存在 {result_path}")
        return False
    
    try:
        # 读取检测结果
        pred_data = csvTools.readCSV(result_path)[1:]  # 跳过标题行
        
        # 获取有检测结果的样本ID（去重）
        pids_with_detections = list(set([row[0] for row in pred_data]))
        
        print(f"发现 {len(pids_with_detections)} 个有检测结果的样本")
        
        # 选择前几个样本用于可视化
        selected_pids = pids_with_detections[:num_samples]
        
        # 确保目录存在
        os.makedirs(os.path.dirname(example_path), exist_ok=True)
        
        # 创建example.csv文件
        with open(example_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for pid in selected_pids:
                writer.writerow([pid])
        
        print(f"已创建 {example_path}，包含 {len(selected_pids)} 个样本:")
        for i, pid in enumerate(selected_pids):
            print(f"  {i+1}. {pid}")
        
        return True
        
    except Exception as e:
        print(f"创建example.csv时出错: {e}")
        return False


def generate_test_anno(anno_dir, test_list_dir, test_anno_dir):
    """生成要可视化图像的标注CSV文件"""
    test_list = csvTools.readCSV(test_list_dir)
    anno_list = csvTools.readCSV(anno_dir)

    test_id_list = []
    for id in test_list:
        test_id_list.append(id[0])

    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(test_anno_dir), exist_ok=True)
        
        with open(test_anno_dir, 'w') as csvfile:
            writer = csv.writer(csvfile)
            for anno in anno_list:
                if anno[0] in test_id_list:
                    writer.writerow([anno[0], anno[1], anno[2], anno[3], anno[4]])
    except Exception as e:
        print("生成标注文件时出错:", e)


def f(data):
    return float(data)


def draw_nms(predicts_list, threshold):
    """非极大值抑制"""
    if len(predicts_list) == 0:
        return []
    
    pd_list = np.array(predicts_list, dtype=np.float32)

    x1 = pd_list[:, 0] - pd_list[:, 3]
    y1 = pd_list[:, 1] - pd_list[:, 3]
    z1 = pd_list[:, 2] - pd_list[:, 3]
    x2 = pd_list[:, 0] + pd_list[:, 3]
    y2 = pd_list[:, 1] + pd_list[:, 3]
    z2 = pd_list[:, 2] + pd_list[:, 3]
    scores = pd_list[:, 4]

    order = scores.argsort()[::-1]

    areas = (x2 - x1 + 1) * (y2 - y1 + 1) * (z2 - z1 + 1)
    keep = []

    while order.size > 0:
        i = order[0]
        keep.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        zz1 = np.maximum(z1[i], z1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        zz2 = np.minimum(z2[i], z2[order[1:]])  # 修正：这里应该是minimum
        inter = np.maximum(0.0, xx2 - xx1 + 1) * np.maximum(0.0, yy2 - yy1 + 1) * np.maximum(0.0, zz2 - zz1 + 1)
        iou_3d = inter / (areas[i] + areas[order[1:]] - inter)
        inds = np.where(iou_3d <= threshold)[0]
        order = order[inds + 1]
    bbox = pd_list[keep]

    return bbox.tolist()


def draw_boxes(filename, pid, gt_list, pred_list, outpath):
    """在CT切片上绘制边界框"""
    try:
        arr, options = nrrd.read(filename)
        png_dir = os.path.join(outpath, pid)
        if not os.path.exists(png_dir):
            os.makedirs(png_dir)

        txt_color = '#000000'
        pred_color = '#FFFFFF'  # 白色：预测框
        gt_color = '#DC143C'    # 红色：真实框

        print(f"为样本 {pid} 生成 {len(arr)} 张切片图像...")
        
        for i, slice_img in enumerate(arr):
            plt.figure(figsize=(8, 8))
            plt.xticks([])
            plt.yticks([])
            plt.axis('off')
            plt.imshow(slice_img, cmap="bone")
            
            # 绘制预测框
            for axis in pred_list:
                start = int(axis[2] - int(axis[3] / 2))
                end = int(axis[2] + int(axis[3] / 2))
                if start <= i <= end:
                    rect = plt.Rectangle(
                        (axis[0] - axis[3] / 2, axis[1] - axis[3] / 2),
                        axis[3], axis[3],
                        fill=False,
                        edgecolor=pred_color,
                        linewidth=2
                    )
                    plt.gca().add_patch(rect)
                    # 修正：使用axis[4]而不是data[4]
                    plt.text(
                        axis[0] - axis[3] / 2, axis[1] - axis[3] / 2,
                        f"{round(axis[4], 2)}",
                        color=txt_color,
                        bbox={'edgecolor': pred_color, 'facecolor': pred_color, 'alpha': 0.5, 'pad': 0}
                    )

            # 绘制真实框
            for data in gt_list:
                start = int(data[2] - int(data[3] / 2))
                end = int(data[2] + int(data[3] / 2))
                if start <= i <= end:
                    rect = plt.Rectangle(
                        (data[0] - data[3] / 2, data[1] - data[3] / 2),
                        data[3], data[3],
                        fill=False,
                        edgecolor=gt_color,
                        linewidth=2
                    )
                    plt.gca().add_patch(rect)

            plt.savefig(os.path.join(png_dir, f"{i}.png"), bbox_inches='tight', dpi=100)
            plt.close()
            
    except Exception as e:
        print(f"处理文件 {filename} 时出错: {e}")


def visualize_detection_results():
    """主要的可视化函数"""
    print("开始生成带检测边界框的CT图像...")
    
    # 配置路径
    anno_dir = data_config['new_annos_dir']
    test_anno_dir = 'annotations/test_anno.csv'
    preprocessed_path = data_config['preprocessed_data_dir']
    val_path = "detection/example.csv"
    out_path = "detection/"
    
    # 修正：使用正确的结果路径
    result_path = 'results/ticnet/2_fold/res/100/FROC/submission_ensemble.csv'
    
    # 自动创建example.csv（如果不存在）
    if not create_example_csv_if_needed(result_path, val_path, num_samples=3):
        return

    print(f"使用检测结果文件: {result_path}")
    
    print("生成测试标注...")
    generate_test_anno(anno_dir, val_path, test_anno_dir)

    print("读取样本列表...")
    pid_list = []
    pid_data = csvTools.readCSV(val_path)
    for i in pid_data:
        pid_list.append(i[0])

    print("读取标注和预测结果...")
    gt_data = csvTools.readCSV(test_anno_dir)
    pred_data = csvTools.readCSV(result_path)[1:]  # 跳过标题行

    print(f"开始处理 {len(pid_list)} 个CT扫描...")
    
    for idx, pid in enumerate(pid_list):
        print(f"\n处理第 {idx+1}/{len(pid_list)} 个样本: {pid}")
        
        # 获取真实标注
        gt_list = []
        for i in gt_data:
            if pid == i[0]:
                data = i[1:]
                gt_list.append(data)

        for i in range(len(gt_list)):
            for j in range(4):
                gt_list[i][j] = f(gt_list[i][j])

        # 获取预测结果
        pred_list = []
        for i in pred_data:
            if pid == i[0]:
                data = i[1:]
                pred_list.append(data)

        for i in range(len(pred_list)):
            for j in range(5):
                pred_list[i][j] = f(pred_list[i][j])

        print(f"找到 {len(gt_list)} 个真实结节, {len(pred_list)} 个预测结节")
        
        # 应用NMS
        pd_list = draw_nms(pred_list, 0.1)
        print(f"NMS后剩余 {len(pd_list)} 个预测结节")
        
        # 尝试不同的文件名格式
        possible_filenames = [
            os.path.join(preprocessed_path, f"{pid}_seg.nrrd"),
            os.path.join(preprocessed_path, f"{pid}.nrrd"),
        ]
        
        filename = None
        for pf in possible_filenames:
            if os.path.exists(pf):
                filename = pf
                break
        
        if filename:
            draw_boxes(filename, pid, gt_list, pd_list, out_path)
            print(f'✓ 完成处理: {filename}')
        else:
            print(f'✗ 文件不存在，尝试了以下路径:')
            for pf in possible_filenames:
                print(f'  - {pf}')

    print(f"\n🎉 可视化完成！")
    print(f"结果保存在 {out_path} 目录下")
    print("每个CT扫描都有一个子文件夹，包含所有切片的PNG图像")
    print("图像中的颜色含义：")
    print("  🔴 红色框：真实的肺结节位置")
    print("  ⚪ 白色框：模型预测的肺结节（带置信度分数）")


if __name__ == "__main__":
    visualize_detection_results()