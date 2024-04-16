
import os
import sys 
import json
import shutil
import subprocess
from PySide2.QtUiTools import QUiLoader
from PySide2 import QtWidgets
from PySide2 import QtCore
from thadam_base import thadam_api

try:
    import maya.cmds as cmds
except ImportError:
    pass

# subtask_path = r"R:\fx_db\publishes\aln\SC_01\ALN_SC_01_SH_0010\FX\cliff_fire"
publish_dir = r"//cdata/3D_LIG/fx_db/publishes"
subtask_dir = r"//cdata/3D_LIG/studio/subtasks"
version_db = "versions_db.json"
subtask_db = 'subtasks.json'

class FXLoader(QtWidgets.QMainWindow):
    
    def __init__(self) -> None:
        
        super().__init__()
        
        self.subtask_path = ''
        dirname = os.path.dirname(__file__)
        ui_file = os.path.join(dirname, 
                               "ui/fxloader.ui"
        )
        ui_loader = QUiLoader()
        self.fx_loader_window = ui_loader.load(ui_file)
        
        self.formLayout = self.fx_loader_window.findChild(QtWidgets.QGridLayout,
                                                              "element_layout")
        self.latest_version_label = self.fx_loader_window.findChild(QtWidgets.QLabel,
                                                              "latest_version")
        self.user_name_label = self.fx_loader_window.findChild(QtWidgets.QLabel,
                                                              "user_name")
        self.comments = self.fx_loader_window.findChild(QtWidgets.QLabel,
                                                              "comments")
        self.show_combo_box = self.fx_loader_window.findChild(
            QtWidgets.QComboBox,
            "show_cbx"
        )
        self.sequence_combo_box = self.fx_loader_window.findChild(
            QtWidgets.QComboBox,
            "seq_cbx"
        )
        seq_combobox_list_view_height = self.sequence_combo_box.view().height()
        self.sequence_combo_box.view().setFixedSize(
                        350,
                        seq_combobox_list_view_height
        )
        
        self.shot_combo_box = self.fx_loader_window.findChild(
            QtWidgets.QComboBox,
            "shot_cbx"
        )
        shot_combo_box_list_view_height = self.sequence_combo_box.view().height()
        self.shot_combo_box.view().setFixedSize(
                        280,
                        shot_combo_box_list_view_height
        )
        self.task_combo_box = self.fx_loader_window.findChild(
            QtWidgets.QComboBox,
            "task_cbx"
        )
        self.sub_task_combo_box = self.fx_loader_window.findChild(
            QtWidgets.QComboBox,
            "subtask_cbx"
        )
        
        self.import_element = self.fx_loader_window.findChild(
            QtWidgets.QPushButton,
            "import_element"
        )
        self.import_element.clicked.connect(self.import_elements)
        
        self.refresh = self.fx_loader_window.findChild(
            QtWidgets.QPushButton,
            "refresh_btn"
        )
        
        self.play_mov_btn = self.fx_loader_window.findChild(
            QtWidgets.QPushButton,
            "play_mov"
        )
        self.play_mov_btn.clicked.connect(self.play_mov)
        
        self.thadam_api_server = thadam_api.ThadamParser()
        self.set_project()
        
        self.show_combo_box.activated[str].connect(self.set_sequence)
        
        seq_args = lambda: self.set_shot(self.show_combo_box.currentText(), 
                                          self.sequence_combo_box.currentText()
        )
        self.sequence_combo_box.activated[str].connect(seq_args)
        self.task_combo_box.activated.connect(self.set_subtask)
        self.sub_task_combo_box.activated.connect(self.generate_elements_entity_widgets)
        self.refresh.clicked.connect(self.generate_elements_entity_widgets)
        
        self.select_all_checkbox = self.fx_loader_window.findChild(QtWidgets.QCheckBox,
                                                              "select_all")
        self.select_all_checkbox.setChecked(True)
        self.select_all_checkbox.stateChanged.connect(self.toggle_element_widget_seelction)
        
        
    def set_project(self) -> None:
        
        """Get All the Projects from thadam server and 
        append to the project combo box
        """
        
        self.show_combo_box.clear()
        self.sequence_combo_box.clear()
        self.shot_combo_box.clear()
        self.task_combo_box.clear()
        self.sub_task_combo_box.clear()
        
        self.projects = self.thadam_api_server.get_projects()
        
        self.projects = sorted(self.projects, key=lambda d: d['proj_code'])
        
        for project in self.projects:
            self.show_combo_box.addItem(project['proj_code'])
            
        self.show_combo_box.setCurrentIndex(-1)
        
    def set_sequence(self, 
                     project_name:str
        )-> None:
        
        """ append all the seq for the given project
        clear all child combo box relative to that
        
        Args:
            project_name(str): project name passed from the 
                        selected project name from the combobox
        """
        
        self.sequence_combo_box.clear()
        self.shot_combo_box.clear()
        self.task_combo_box.clear()
        self.sub_task_combo_box.clear()
        self.clear_widgets_in_form_layout()
        self.latest_version_label.clear()
        self.user_name_label.clear()
        self.comments.clear()
        
        sequences = set()
        self.get_sequences = self.thadam_api_server.get_sequences(project_name)
        for sequence in self.get_sequences:
            sequences.add(sequence['seq_name']) 
        
        for sequence in sorted(sequences):
            self.sequence_combo_box.addItem(sequence)
        
        self.sequence_combo_box.setCurrentIndex(-1)
    
    def set_shot(self, 
                 project_name: str,
                 seq_name: str) -> None:
        
        """Append shots for the given project name and seq name
        
        Args:
            project_name(str): User selected project in project combobox
            seq_name(str): user selected seq in seq combobox
        """
        
        self.shot_combo_box.clear()
        self.task_combo_box.clear()
        self.sub_task_combo_box.clear()
        self.clear_widgets_in_form_layout()
        self.latest_version_label.clear()
        self.user_name_label.clear()
        self.comments.clear()
        
        self.shots = self.thadam_api_server.get_shots(project_name,
                                                    seq_name
        )
        
        self.shots = sorted(self.shots, key=lambda d: d['shot_name'])
        for shot in self.shots:
            self.shot_combo_box.addItem(shot['shot_name'])
        
        self.shot_combo_box.setCurrentIndex(-1)
        self.shot_combo_box.activated[str].connect(self.set_task)
    
    def set_task(self) -> None:
        
        """Append Task names and allow user to select from the 
        combobox of task
        """
        self.task_combo_box.clear()
        self.sub_task_combo_box.clear()
        self.clear_widgets_in_form_layout()
        self.latest_version_label.clear()
        self.user_name_label.clear()
        self.comments.clear()
        
        tasks = set()
        get_selected_project_name = self.show_combo_box.currentText()
        get_selected_shot = self.shot_combo_box.currentText()
        
        for project in self.projects:
            if project['proj_code'] == get_selected_project_name:
                get_selected_show_id = project['proj_id']
            
        for shots in self.shots:
            if shots['shot_name'] == get_selected_shot:
                get_selected_shot_id = shots['scope_id']

        self.task_types = self.thadam_api_server.get_tasks(
                                                    get_selected_project_name,
                                                    get_selected_show_id,
                                                    get_selected_shot_id
        )
            
        for task_types in self.task_types:
            tasks.add(task_types['type_name'])
        for task_types in sorted(tasks):
            self.task_combo_box.addItem(task_types)
        self.task_combo_box.setCurrentIndex(-1)
       
    
    def set_subtask(self) ->None:
        
            self.subtaskpath = os.path.join(
                subtask_dir,
                self.show_combo_box.currentText(),
                self.sequence_combo_box.currentText(),
                self.shot_combo_box.currentText(),
                self.task_combo_box.currentText()
            )
            subask_json = os.path.join(self.subtaskpath,
                                       subtask_db)
            
            try:
                for sub_task in self.read_json(subask_json):
                    self.sub_task_combo_box.addItem(sub_task)
                self.sub_task_combo_box.setCurrentIndex(-1)
            except Exception:
                QtWidgets.QMessageBox.warning(self,
                                              "FX Loader", 
                                              "Sub-Task Not Found For Given Scope!!")
                self.task_combo_box.setCurrentIndex(-1)
                self.sub_task_combo_box.clear()
                self.clear_widgets_in_form_layout()
                self.latest_version_label.clear()
                self.user_name_label.clear()
                self.comments.clear()
        
    
    @staticmethod
    def read_json(json_file):
        
        with open(json_file, 'r') as f:
            data = json.load(f)
        return data
    
    def entity_validation(self) -> bool:
        
        if all(
            [self.show_combo_box.currentText(),
            self.sequence_combo_box.currentText(),
            self.shot_combo_box.currentText(),
            self.task_combo_box.currentText(),
            self.sub_task_combo_box.currentText()]
        ):
            return True
        else:
            QtWidgets.QMessageBox.warning(self,
                                              "FX Loader", 
                                              "All Fields Needed to be Selected!!")
            return False
        
    def get_latest_subtask_json(self) -> None:
        
        self.subtask_path = os.path.join(
            publish_dir,
            self.show_combo_box.currentText(),
            self.sequence_combo_box.currentText().split('/')[-1],
            self.shot_combo_box.currentText(),
            self.task_combo_box.currentText(),
            self.sub_task_combo_box.currentText(),
        )

        versions_db_file = os.path.join(self.subtask_path, version_db)
        if os.path.exists(versions_db_file):
            version_db_data = self.read_json(versions_db_file)
            latest_json = set()
            versions_list = []
            for elements_keys in version_db_data.keys():
                for element_key in version_db_data[elements_keys]:
                    versions_list.append(element_key)
            max_version_json = max(versions_list)
            
            for elements_key in version_db_data.keys():
                if max_version_json in version_db_data[elements_key]:
                    latest_json.add(version_db_data[elements_key][max_version_json])

            self.subtask_latest_json = os.path.join(self.subtask_path,
                                            list(latest_json)[0])
            
            self.subtask_latest_json_data = self.read_json(self.subtask_latest_json)
            return True
        else:
            self.clear_widgets_in_form_layout()
    
    def generate_elements_entity_widgets(self) -> None:
        
        if self.entity_validation():
            if self.get_latest_subtask_json():
                self.init_element_gui()
        
    def clear_widgets_in_form_layout(self) -> None:
        
        # Remove the widgets each time it refreshes 
        widgets = []
        for i in range(self.formLayout.count()):
            child = self.formLayout.itemAt(i).widget()
            widgets.append(child)
        for widget in widgets:
            widget.deleteLater()
                        
    def init_element_gui(self) -> None:
        
        self.latest_version_label.clear()
        self.user_name_label.clear()
        
        self.clear_widgets_in_form_layout()
        
        label_text = self.latest_version_label.text()
        self.latest_version_label.setText(label_text + \
                                        "Latest Version:    "  +  \
                                        str(self.subtask_latest_json_data['subtask_version'])
        )
        self.user_name_label.setText("Published By:   " + \
                                    str(self.subtask_latest_json_data['user'])
        )
        self.comments.setText(
                            "Comments:   " + \
                            self.subtask_latest_json_data['comments']
        )

        self.scroll_area = QtWidgets.QScrollArea()
        self.master_grp_box = QtWidgets.QGroupBox()
        self.master_grp_box.setObjectName("master_element_grp_box")
        self.master_grp_box.setStyleSheet("""
QGroupBox#master_element_grp_box {
    font: 11pt "Microsoft YaHei UI";
    border: 1px solid black;
    border-radius: 5px;
}
        """)
        self.elements_vertical_layout = QtWidgets.QVBoxLayout()
        self.elements_vertical_layout.setSpacing(25)
        
        for element_name, element_dict in self.subtask_latest_json_data['cache_names'].items():
            self.elements_grp_box = QtWidgets.QGroupBox(element_name)
            self.elements_grp_box.setStyleSheet("""
QGroupBox {
    font: 11pt "Microsoft YaHei UI";
    border: 1px solid black;
    border-radius: 10px;
}
QGroupBox::title{
	left: 20px;
}
        """)
            self.elements_grp_box.setCheckable(True)
            self.elements_grp_box.setFixedSize(990,150)

            # hbox_layout = QtWidgets.QHBoxLayout()
            vbox_layout = QtWidgets.QVBoxLayout()
            vbox_layout.addStretch(8)
            vbox_layout.setSpacing(10)
            # vbox_layout.setContentsMargins(8, 0, 0 , 0)
            
            cache_type_label = QtWidgets.QLabel("Cache Type:    " + element_dict['cache_type'])
            cache_type_label.setStyleSheet("font: 25 9pt 'Bahnschrift Light'")
            
            frame_range_label = QtWidgets.QLabel("Frame Range:      " + element_dict['frame_range'])
            frame_range_label.setStyleSheet("font: 25 9pt 'Bahnschrift Light'")
            
            publish_category_label = QtWidgets.QLabel("Publish Category:      " + element_dict['publish_category'])
            publish_category_label.setStyleSheet("font: 25 9pt 'Bahnschrift Light'")
            
            publish_path_label = QtWidgets.QLineEdit(element_dict['publish_path'])
            publish_path_label.setStyleSheet("font: 25 9pt 'Bahnschrift Light'")
            publish_path_label.setReadOnly(True)
            
            vbox_layout.addWidget(cache_type_label)
            vbox_layout.addWidget(frame_range_label)
            vbox_layout.addWidget(publish_category_label)
            vbox_layout.addWidget(publish_path_label)
            
            # self.elements_grp_box.setLayout(hbox_layout)
            self.elements_grp_box.setLayout(vbox_layout)
            
            self.elements_vertical_layout.addWidget(self.elements_grp_box)
            

        self.scroll_area.setWidget(self.master_grp_box)
        self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)

        self.master_grp_box.setLayout(self.elements_vertical_layout)
        self.formLayout.addWidget(self.scroll_area)
    
    def toggle_element_widget_seelction(self, check_value): 
        
        state = QtCore.Qt.CheckState(check_value)
        for groupboxes in self.master_grp_box.findChildren(QtWidgets.QGroupBox):
            if state == QtCore.Qt.CheckState.Checked:
                groupboxes.setChecked(True)
            elif state == QtCore.Qt.CheckState.Unchecked:
                groupboxes.setChecked(False)


    def import_elements(self) -> None:
        
        for widgets in range(self.formLayout.count()):
            scroll_area = self.formLayout.itemAt(widgets).widget()
            master_element_grp = scroll_area.widget()
            for element_grpboxes in master_element_grp.findChildren(QtWidgets.QGroupBox):
                if element_grpboxes.isChecked():
                    user_selected_element_name = element_grpboxes.title()
                    if self.subtask_latest_json_data['cache_names']\
                                                    [user_selected_element_name]\
                                                    ['cache_type'] == 'vdb':
                        vdb_publish_path = self.subtask_latest_json_data['cache_names']\
                                                                    [user_selected_element_name]\
                                                                    ['publish_path']
                        vdb_file = [vdbfiles \
                                    for vdbfiles in os.listdir(vdb_publish_path) \
                                    if vdbfiles.endswith('.vdb')][0]
                        
                        vdb_file = os.path.join(vdb_publish_path, vdb_file)
                        volume_container = cmds.createNode('aiVolume')
                        volume_container_element_name = cmds.rename(volume_container, user_selected_element_name)
                        cmds.setAttr('%s.filename' %volume_container_element_name, 
                                     vdb_file, 
                                     type='string'
                                    )
                        cmds.setAttr('%s.useFrameExtension' %volume_container_element_name,1)
                    
                    if self.subtask_latest_json_data['cache_names']\
                                                    [user_selected_element_name]\
                                                    ['cache_type'] == 'abc':
                        abc_publish_path = self.subtask_latest_json_data['cache_names']\
                                                                    [user_selected_element_name]\
                                                                    ['publish_path']
                        abc_file = [abcfiles \
                                    for abcfiles in os.listdir(abc_publish_path) \
                                    if abcfiles.endswith('.abc')][0]
                        abc_file = os.path.join(abc_publish_path, abc_file)
                        cmds.AbcImport(abc_file, mode='import')
    
    def play_mov(self) -> None:
        
        mr_viewer = r"C:\Program Files\mrViewer-v5.9.8-Windows-64\bin\mrViewer.exe"
        if not shutil.which(mr_viewer):
            QtWidgets.QMessageBox.information(self,
                                            "FX Loader", 
                                            f"mrViewer not installed in below path!!\n\n{mr_viewer}")
        else:
            if self.entity_validation():
                self.get_latest_subtask_json()
                if not self.subtask_latest_json_data['mov_path']:
                    QtWidgets.QMessageBox.information(self,
                                                "FX Loader", 
                                                "Mov Not Found")
                else:
                    mov = self.subtask_latest_json_data['mov_path'].replace(r"/", os.sep)
                    print("playing: ",mr_viewer, mov)
                    subprocess.Popen("\"%s\" %s" %(mr_viewer, mov),
                                    shell=True)
        

if __name__ == "__main__":
    
    app = QtWidgets.QApplication(sys.argv)
    fx_loader = FXLoader()
    fx_loader.fx_loader_window.show()
    app.exec_()
else:
    app = QtWidgets.QApplication.instance()
    for widget in app.topLevelWidgets():
        if widget.objectName() == "fxloader":
            widget.close()
    fx_loader = FXLoader()
    fx_loader.fx_loader_window.show()
    
    # import sys
    # sys.path.append(r"\\cdata\3D_LIG\studio\pipeline\internal\apps\maya\2022")
    # sys.path.append(r"\\cdata\3D_LIG\studio\pipeline\internal\common")
    # import fx_loader
    # reload(fx_loader)
    # fx_loader1 = fx_loader.FXLoader()
    # fx_loader1.fx_loader_window.show()