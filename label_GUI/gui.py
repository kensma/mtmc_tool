import sys
import time
import threading
import os
import shutil
import yaml
import cv2

from collate_output import collate
from interpolation import interpolation
from smooth import smooth
from plotVideo import PlotVideoMulti

from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QAction, QImage, QKeySequence, QPixmap, QMouseEvent
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QCheckBox,
    QApplication,
    QDialog,
    QTabWidget,
    QLineEdit,
    QDialogButtonBox,
    QFrame,
    QListWidget,
    QGroupBox,
    QPushButton,
    QHBoxLayout,
    QSizePolicy,
    QButtonGroup,
    QRadioButton,
    QGridLayout,
    QSlider,
    QMessageBox
)

SHOW_SIZE = (1440, 810)
x_ratio, y_ratio = 1920 / SHOW_SIZE[0], 1080 / SHOW_SIZE[1]

class Thread(QThread):
    updateFrame = Signal(QImage)

    def __init__(self, cfg_file, target_dir, parent=None):
        QThread.__init__(self, parent)
        self.status = True

        config = yaml.load(open(cfg_file, 'r'), Loader=yaml.FullLoader)
        config['target_path'] = target_dir
        self.run_path = config['run_path']
        self.max_frame_id = config['max_frame_id']
        self.plot_video = PlotVideoMulti(config)

    def run(self):

        while self.status:
            reslut = self.plot_video.get_plot_frame()

            if reslut is None:
                continue

            self.frame_id, frame = reslut

            # Reading the image in RGB to display it
            if frame is None:
                continue
            color_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Creating and scaling QImage
            h, w, ch = color_frame.shape
            img = QImage(color_frame.data, w, h, ch * w, QImage.Format_RGB888)
            scaled_img = img.scaled(*SHOW_SIZE, Qt.KeepAspectRatio)

            # Emit signal
            self.updateFrame.emit(scaled_img)


class Window(QDialog):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        tab_widget = QTabWidget()
        tab_widget.addTab(PreProcessingTab(self, ), "前處理")
        tab_widget.addTab(BeBugTab(self, ), "錯誤修正")


        main_layout = QVBoxLayout()
        main_layout.addWidget(tab_widget)
        self.setLayout(main_layout)
        self.setWindowTitle("Tab Dialog")

class PreProcessingTab(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        cfg_label = QLabel("設定檔案:")
        self.cfg_edit = QLineEdit()

        save_dir_label = QLabel("儲存資料夾:")
        self.save_dir_edit = QLineEdit("preProcessing")

        step_label = QLabel("步驟選擇:")
        self.collate_checkbox = QCheckBox("整理軌跡")
        self.interpolation_checkbox = QCheckBox("補中間斷掉的軌跡")
        self.smooth_checkbox = QCheckBox("平滑軌跡")

        self.collate_checkbox.setChecked(True)
        self.interpolation_checkbox.setChecked(False)
        self.smooth_checkbox.setChecked(True)

        step_layout = QHBoxLayout()
        step_layout.addWidget(step_label)
        step_layout.addWidget(self.collate_checkbox)
        step_layout.addWidget(self.interpolation_checkbox)
        step_layout.addWidget(self.smooth_checkbox)

        max_miss_dir_label = QLabel("補軌跡最大遺失幀數:")
        self.max_miss_dir_edit = QLineEdit("60")

        self.button = QPushButton("確定")

        self.message_label = QLabel("")

        self.button.clicked.connect(self.btn_click)

        main_layout = QVBoxLayout()
        main_layout.addWidget(cfg_label)
        main_layout.addWidget(self.cfg_edit)
        main_layout.addWidget(save_dir_label)
        main_layout.addWidget(self.save_dir_edit)
        main_layout.addLayout(step_layout)
        main_layout.addWidget(max_miss_dir_label)
        main_layout.addWidget(self.max_miss_dir_edit)
        main_layout.addWidget(self.button)
        main_layout.addWidget(self.message_label)
        main_layout.addStretch(1)
        self.setLayout(main_layout)

        self.button.setFocusPolicy(Qt.NoFocus)

    @Slot()
    def btn_click(self):
        self.button.setText("處理中...")
        self.button.setStyleSheet("background-color: orange;")
        self.button.setEnabled(False)

        threading.Thread(target=self.run).start()

    def run(self):
        cfg_path = os.path.join('cfg', self.cfg_edit.text())
        config = yaml.load(open(cfg_path, 'r'), Loader=yaml.FullLoader)

        cam_infos = config['cam_infos']
        run_path = config['run_path']
        prev_path = os.path.join(run_path, config['target_path'])

        # 整理軌跡輸出
        if self.collate_checkbox.isChecked():
            collate_save_path = os.path.join("cache", "collate")
            collate(cam_infos, prev_path, collate_save_path)
            prev_path = collate_save_path

        # 補中間斷掉的軌跡
        if self.interpolation_checkbox.isChecked():
            interpolation_save_path = os.path.join("cache", "interpolation")
            interpolation(cam_infos, prev_path, interpolation_save_path, int(self.max_miss_dir_edit.text()))
            prev_path = interpolation_save_path

        # 平滑軌跡
        if self.smooth_checkbox.isChecked():
            smooth_save_path = os.path.join("cache", "smooth")
            smooth(cam_infos, prev_path, smooth_save_path)
            prev_path = smooth_save_path

        shutil.copytree(prev_path, os.path.join(run_path, self.save_dir_edit.text()))

        if os.path.exists("cache"):
            shutil.rmtree("cache")
        os.mkdir("cache")

        self.button.setText("確定")
        self.button.setStyleSheet("")
        self.button.setEnabled(True)

        self.message_label.setText("完成")

class BeBugTab(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.status = False
        self.is_select = False
        self.control_status = False
        self.select_cam = None
        self.select_local_id = None
        self.select_global_id = None
        self.select_frame_id = None

        #region 影像顯示區
        self.VideoWidget = QLabel()
        self.VideoWidget.setFixedSize(*SHOW_SIZE)

        self.VideoWidget.setStyleSheet("background-color: gray;")

        self.VideoWidget.mousePressEvent = self.labelMousePressEvent
        #endregion

        #region 設定檔&儲存位置
        self.group_file = QGroupBox("設定檔&儲存位置")
        self.group_file.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.file_layout = QVBoxLayout()

        cfg_label = QLabel("設定檔案:")
        self.cfg_edit = QLineEdit()

        preProcess_dir_label = QLabel("前處理資料夾:")
        self.preProcess_dir_edit = QLineEdit("preProcessing")

        save_dir_label = QLabel("儲存資料夾:")
        self.save_dir_edit = QLineEdit(f"gt-{time.strftime('%Y%m%d%H%M%S')}")

        self.file_layout.addWidget(cfg_label)
        self.file_layout.addWidget(self.cfg_edit)
        self.file_layout.addWidget(preProcess_dir_label)
        self.file_layout.addWidget(self.preProcess_dir_edit)
        self.file_layout.addWidget(save_dir_label)
        self.file_layout.addWidget(self.save_dir_edit)
        self.file_layout.addStretch(1)

        self.group_file.setLayout(self.file_layout)
        #endregion

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.VideoWidget)
        top_layout.addWidget(self.group_file)

        #region 編輯選項
        self.group_edit = QGroupBox("編輯選項")
        self.group_edit.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.edit_layout = QGridLayout()

        range_label = QLabel("選擇變更範圍:   ")
        self.range_btn_group = QButtonGroup(self)
        range_full = QRadioButton("整段軌跡", self)
        range_from_frame = QRadioButton("從這幀", self)
        self.range_btn_group.addButton(range_full, 0)
        self.range_btn_group.addButton(range_from_frame, 1)
        range_full.setChecked(True)

        range_layout = QVBoxLayout()
        range_layout.addWidget(range_label)
        range_layout.addWidget(range_full)
        range_layout.addWidget(range_from_frame)

        id_label = QLabel("選擇變更id:")
        local_label = QLabel("local:\t")
        self.id_local_edit = QLineEdit("0")
        local_layout = QHBoxLayout()
        local_layout.addWidget(local_label)
        local_layout.addWidget(self.id_local_edit)
        global_label = QLabel("global:\t")
        self.id_global_edit = QLineEdit("0")
        global_layout = QHBoxLayout()
        global_layout.addWidget(global_label)
        global_layout.addWidget(self.id_global_edit)

        id_layout = QVBoxLayout()
        id_layout.addWidget(id_label)
        id_layout.addLayout(local_layout)
        id_layout.addLayout(global_layout)

        edit_buttons_layout = QHBoxLayout()
        self.btn_confirmed = QPushButton("儲存")
        self.btn_clone = QPushButton("取消")
        edit_buttons_layout.addWidget(self.btn_confirmed)
        edit_buttons_layout.addWidget(self.btn_clone)
        edit_buttons_layout.addStretch(1)

        self.edit_layout.addLayout(range_layout, 0, 0)
        self.edit_layout.addLayout(id_layout, 0, 1, 0, 2)
        self.edit_layout.addLayout(edit_buttons_layout, 0, 3)

        self.group_edit.setLayout(self.edit_layout)
        self.group_edit.setEnabled(False)

        self.btn_confirmed.clicked.connect(self.confirmedBtnClicked)
        self.btn_clone.clicked.connect(self.cloneBtnClicked)
        #endregion

        #region 控制
        self.group_control = QGroupBox("控制")
        self.group_control.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        control_layout = QVBoxLayout()

        self.btn_control1 = QPushButton("前30幀 (←)")
        self.btn_control2 = QPushButton("前1幀 (d)")
        self.btn_control3 = QPushButton("暫停/開始 (space)")
        self.btn_control4 = QPushButton("後1幀 (f)")
        self.btn_control5 = QPushButton("後30幀 (→)")

        control_btn_layout = QHBoxLayout()
        control_btn_layout.addWidget(self.btn_control1)
        control_btn_layout.addWidget(self.btn_control2)
        control_btn_layout.addWidget(self.btn_control3)
        control_btn_layout.addWidget(self.btn_control4)
        control_btn_layout.addWidget(self.btn_control5)

        self.control_slider = QSlider(Qt.Horizontal)
        self.control_slider.sliderReleased.connect(self.controlSliderChanged)

        control_layout.addLayout(control_btn_layout)
        control_layout.addWidget(self.control_slider)

        self.group_control.setLayout(control_layout)

        self.changeControl(False)

        self.btn_control1.clicked.connect(lambda x: self.control('prev_30_frame'))
        self.btn_control2.clicked.connect(lambda x: self.control('prev_frame'))
        self.btn_control3.clicked.connect(lambda x: self.control('pauseAndStart'))
        self.btn_control4.clicked.connect(lambda x: self.control('next_frame'))
        self.btn_control5.clicked.connect(lambda x: self.control('next_30_frame'))

        buttons_layout = QHBoxLayout()
        self.btn_start = QPushButton("開始")
        self.btn_stop = QPushButton("儲存")
        self.btn_start.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.btn_stop.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        buttons_layout.addWidget(self.btn_stop)
        buttons_layout.addWidget(self.btn_start)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.group_control)
        bottom_layout.addLayout(buttons_layout)

        self.btn_start.clicked.connect(self.start)
        self.btn_stop.clicked.connect(self.saveBtncilcked)
        self.btn_stop.setEnabled(False)
        #endregion
        
        main_layout = QVBoxLayout()
        # main_layout.addWidget(self.VideoWidget, 0)
        # main_layout.addWidget(self.group_file, 1)
        main_layout.addLayout(top_layout, 0)
        main_layout.addWidget(self.group_edit, 1)
        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

        # 確認是否儲存
        self.save_box = QMessageBox()
        self.save_box.setWindowTitle("儲存")
        self.save_box.setText("是否儲存?")
        self.save_box.setStandardButtons( QMessageBox.Cancel | QMessageBox.Discard | QMessageBox.Save)
        self.save_box.setDefaultButton(QMessageBox.Save)
        self.save_box.button(QMessageBox.Cancel).setText("取消")
        self.save_box.button(QMessageBox.Discard).setText("不儲存")
        self.save_box.button(QMessageBox.Save).setText("儲存")

        # 確認檔案覆蓋
        self.cover_box = QMessageBox()
        self.cover_box.setWindowTitle("以存在檔案")
        self.cover_box.setText("是否覆蓋?")
        self.cover_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        self.cover_box.setDefaultButton(QMessageBox.No)

        # 警告衝突
        self.conflict_box = QMessageBox()
        self.conflict_box.setWindowTitle("ID衝突")
        self.conflict_box.setStandardButtons(QMessageBox.Ok)

    def start(self):
        print("Starting...")
        self.setFocus()
        self.btn_stop.setEnabled(True)
        self.btn_start.setEnabled(False)

        self.th = Thread(self.cfg_edit.text(), self.preProcess_dir_edit.text(), self)
        self.th.finished.connect(self.close)
        self.th.updateFrame.connect(self.setImage)
        self.th.start()

        self.control_slider.setRange(0, self.th.max_frame_id)

        self.control_func = {
            'prev_30_frame': self.th.plot_video.prev_30_frame,
            'prev_frame': self.th.plot_video.prev_frame,
            'pauseAndStart': self.th.plot_video.pauseAndStart,
            'next_frame': self.th.plot_video.next_frame,
            'next_30_frame': self.th.plot_video.next_30_frame
        }

        self.changeControl(True)
        self.group_file.setEnabled(False)

        self.status = True

    def saveBtncilcked(self):
        save_box_ret = self.save_box.exec()
        print("關閉...")
        if save_box_ret == QMessageBox.Cancel:
            return
        elif save_box_ret == QMessageBox.Save:
            save_dir = self.save_dir_edit.text()
            save_path = os.path.join(self.th.run_path, save_dir)
            if os.path.exists(save_path) and len(os.listdir(save_path)):
                cover_box_ret = self.cover_box.exec()
                if cover_box_ret == QMessageBox.No:
                    return
            self.th.plot_video.save_target(save_dir)
        self.changeControl(False)
        self.btn_stop.setEnabled(False)
        self.group_edit.setEnabled(False)
        self.th.status = False
        self.th.wait()
        self.btn_start.setEnabled(True)
        self.group_file.setEnabled(True)
        print("關閉完成")

    @Slot(QImage)
    def setImage(self, image):
        self.control_slider.setValue(self.th.frame_id)
        self.VideoWidget.setPixmap(QPixmap.fromImage(image))

    def labelMousePressEvent(self, event: QMouseEvent):
        if not self.status:
            return
        self.control('pauseAndStart')
        pos = event.position().toPoint().toTuple()
        true_pos = [pos[0]*x_ratio, pos[1]*y_ratio]
        if self.is_select:
            cam, local_id, global_id = self.th.plot_video.get_click_bbox(true_pos, False)
            if local_id is None:
                return
            self.id_local_edit.setText(str(local_id))
            self.id_global_edit.setText(str(global_id))
        else:
            cam, local_id, global_id = self.th.plot_video.get_click_bbox(true_pos, True)
            if local_id is None:
                return
            self.group_edit.setEnabled(True)
            self.id_local_edit.setText(str(local_id))
            self.id_global_edit.setText(str(global_id))
            self.is_select = True
            self.select_cam = cam
            self.select_local_id = local_id
            self.select_global_id = global_id
            self.select_frame_id = self.th.plot_video.frame_id - 1
            self.changeControl(False)

    def keyPressEvent(self, event):
        if not self.status:
            return
        key = event.key()
        if self.control_status:
            if key == Qt.Key_Space:
                self.control('pauseAndStart')
            elif key == Qt.Key_F:
                self.control('next_frame')
            elif key == Qt.Key_D:
                self.control('prev_frame')
            elif key == Qt.Key_Right:
                self.control('next_30_frame')
            elif key == Qt.Key_Left:
                self.control('prev_30_frame')

    def control(self, func_name):
        self.control_func[func_name]()
    
    def changeControl(self, status):
        self.control_status = status
        self.group_control.setEnabled(status)

    def confirmedBtnClicked(self):
        from_frame = self.select_frame_id if self.range_btn_group.checkedId() == 1 else None
        local_id = int(self.id_local_edit.text()) if self.id_local_edit.text() != "" and int(self.id_local_edit.text()) != self.select_local_id else None
        global_id = int(self.id_global_edit.text()) if self.id_global_edit.text() != "" and int(self.id_global_edit.text()) != self.select_global_id else None

        is_conflict, conflict_frame , conflict_id_type = self.th.plot_video.check_conflict(self.select_cam, self.select_local_id, local_id, global_id, from_frame)

        if is_conflict:
            self.conflict_box.setText(f'在第{conflict_frame}幀發現{conflict_id_type} id衝突')
            self.conflict_box.exec()
            return

        self.th.plot_video.change_id(self.select_cam, self.select_local_id, local_id, global_id, from_frame)
        self.cloneBtnClicked()
    
    def cloneBtnClicked(self):
        self.is_select = False
        self.group_edit.setEnabled(False)
        self.control('next_frame')
        self.setFocus()
        self.changeControl(True)

    def controlSliderChanged(self):
        if not self.status:
            return
        self.th.plot_video.to_frame(self.control_slider.value())


if __name__ == "__main__":
    if os.path.exists("cache"):
        shutil.rmtree("cache")
    os.mkdir("cache")
    app = QApplication(sys.argv)

    tab_dialog = Window()
    # tab_dialog.resize(800, 600)
    tab_dialog.show()

    sys.exit(app.exec())