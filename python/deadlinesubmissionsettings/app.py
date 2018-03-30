import sys
# import pprint

from avalon import api, io
from avalon.tools import lib as tools_lib
from avalon.vendor.Qt import QtWidgets, QtCore
from avalon.vendor import qtawesome as qta

from . import lib
from . import mayalib

module = sys.modules[__name__]
module.window = None


class App(QtWidgets.QWidget):
    """Main application for alter settings per render job (layer)"""

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.setWindowTitle("Deadline Submission setting")
        self.setFixedSize(250, 480)

        self.setup_ui()
        self.connections()
        self.create_machine_limit_options()

        # Apply any settings based off the renderglobalsDefault instance
        self._apply_settings()

    def setup_ui(self):
        """Build the initial UI"""

        MULTI_SELECT = QtWidgets.QAbstractItemView.ExtendedSelection

        layout = QtWidgets.QVBoxLayout(self)

        publish = QtWidgets.QCheckBox("Suspend Publish Job")
        defaultlayer = QtWidgets.QCheckBox("Include Default Render Layer")
        run_slap_comp = QtWidgets.QCheckBox("Run Slap Comp")

        brows_hlayout = QtWidgets.QHBoxLayout()
        file_line = QtWidgets.QLineEdit()

        brows_icon = qta.icon("fa.folder", color="white")
        brows_btn = QtWidgets.QPushButton()
        brows_btn.setIcon(brows_icon)

        file_line.setPlaceholderText("<Slap Comp File>")
        file_line.setEnabled(False)
        brows_btn.setEnabled(False)

        brows_hlayout.addWidget(file_line)
        brows_hlayout.addWidget(brows_btn)

        # region Priority
        priority_grp = QtWidgets.QGroupBox("Priority")
        priority_hlayout = QtWidgets.QHBoxLayout()

        priority_value = QtWidgets.QSpinBox()
        priority_value.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        priority_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        priority_slider.setMinimum(0)
        priority_slider.setMaximum(99)

        priority_hlayout.addWidget(priority_value)
        priority_hlayout.addWidget(priority_slider)
        priority_grp.setLayout(priority_hlayout)
        # endregion Priority

        # Group box for type of machine list
        list_type_grp = QtWidgets.QGroupBox("Machine List Type")
        list_type_hlayout = QtWidgets.QHBoxLayout()

        black_list = QtWidgets.QRadioButton("Blacklist")
        black_list.setChecked(True)
        black_list.setToolTip("List machines which the job WILL NOT use")

        white_list = QtWidgets.QRadioButton("Whitelist")
        white_list.setToolTip("List machines which the job WILL use")

        list_type_hlayout.addWidget(black_list)
        list_type_hlayout.addWidget(white_list)
        list_type_grp.setLayout(list_type_hlayout)

        # region Machine selection
        machines_hlayout = QtWidgets.QHBoxLayout()
        machines_hlayout.setSpacing(2)
        machine_list = QtWidgets.QListWidget()
        listed_machines = QtWidgets.QListWidget()

        # Buttons
        button_vlayout = QtWidgets.QVBoxLayout()
        button_vlayout.setAlignment(QtCore.Qt.AlignCenter)
        button_vlayout.setSpacing(4)

        add_machine_btn = QtWidgets.QPushButton(">")
        add_machine_btn.setFixedWidth(25)

        remove_machine_btn = QtWidgets.QPushButton("<")
        remove_machine_btn.setFixedWidth(25)

        button_vlayout.addWidget(add_machine_btn)
        button_vlayout.addWidget(remove_machine_btn)

        machines_hlayout.addWidget(machine_list)
        machines_hlayout.addLayout(button_vlayout)
        machines_hlayout.addWidget(listed_machines)

        # Machine selection widget settings
        machine_list.setSelectionMode(MULTI_SELECT)
        listed_machines.setSelectionMode(MULTI_SELECT)

        # endregion
        accept_btn = QtWidgets.QPushButton("Use Settings")

        layout.addWidget(defaultlayer)
        layout.addWidget(publish)
        layout.addWidget(run_slap_comp)
        layout.addLayout(brows_hlayout)
        layout.addWidget(priority_grp)
        layout.addWidget(list_type_grp)
        layout.addLayout(machines_hlayout)
        layout.addWidget(accept_btn)

        # Enable access for all methods
        self.publish = publish
        self.defaultlayer = defaultlayer
        self.run_slap_comp = run_slap_comp
        self.flow_file = file_line
        self.browse_file_btn = brows_btn
        self.priority_value = priority_value
        self.priority_slider = priority_slider
        self.black_list = black_list
        self.white_list = white_list
        self.machine_list = machine_list
        self.listed_machines = listed_machines
        self.add_machine_btn = add_machine_btn
        self.remove_machine_btn = remove_machine_btn
        self.accept = accept_btn

        self.setLayout(layout)

    def connections(self):

        self.run_slap_comp.toggled.connect(self.on_run_slap_comp_toggled)
        self.browse_file_btn.clicked.connect(self.on_browse_clicked)

        self.priority_slider.valueChanged[int].connect(
            self.priority_value.setValue)

        self.priority_value.valueChanged.connect(self.priority_slider.setValue)

        self.add_machine_btn.clicked.connect(self.add_selected_machines)
        self.remove_machine_btn.clicked.connect(self.remove_selected_machines)
        self.accept.clicked.connect(self.parse_settings)

        self.priority_slider.setValue(50)

    def on_run_slap_comp_toggled(self):
        state = self.run_slap_comp.isChecked()
        self.flow_file.setEnabled(state)
        self.browse_file_btn.setEnabled(state)

    def on_browse_clicked(self):

        workdir = lib.get_work_directory()
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Choose comp", workdir, filter="*.comp")

        if not file_path:
            return

        self.flow_file.setText(file_path)

    def add_selected_machines(self):
        """Add selected machines to the list which is going to be used"""

        # Get currently list machine for use
        listed_machines = self._get_listed_machines()

        # Get all machines selected from available
        machines = self.machine_list.selectedItems()
        for machine in machines:
            # Check if name is already in use
            machine_name = machine.text()
            if machine_name in listed_machines:
                continue
            # Add to list of machines to use
            self.listed_machines.addItem(machine_name)

    def remove_selected_machines(self):
        machines = self.listed_machines.selectedItems()
        for machine in machines:
            self.listed_machines.takeItem(self.listed_machines.row(machine))

    def create_machine_limit_options(self):
        """Build the checks for the machine limit"""

        for name in lib.get_machine_list():
            self.machine_list.addItem(name)

    def refresh(self):

        self.machine_list.clear()
        self.create_machine_limit_options()

    def parse_settings(self):

        # Get UI settings as dict
        job_info = {}

        machine_limits = self._get_listed_machines()
        machine_limits = " ".join(machine_limits)

        job_info["priority"] = self.priority_value.value()
        job_info["suspendPublishJob"] = self.publish.isChecked()
        job_info["includeDefaultRenderLayer"] = self.defaultlayer.isChecked()
        row_slap_coml = self.run_slap_comp.isChecked()
        if row_slap_coml:
            job_info["runSlapComp"] = row_slap_coml
            job_info["flowFile"] = self.flow_file.text()

        job_info["whitelist"] = self._get_list_type()
        job_info["machineList"] = machine_limits

        # Get the  node and apply settings
        instance = mayalib.find_render_instance()
        if not instance:
            self.renderglobals_message()
            return

        mayalib.apply_settings(instance, job_info)

    def renderglobals_message(self):

        message = ("Please use the Creator from the Avalon menu to create"
                   "a renderglobalsDefault instance")

        button = QtWidgets.QMessageBox.StandardButton.Ok

        QtWidgets.QMessageBox.critical(self,
                                       "Missing instance",
                                       message,
                                       button)
        return

    def _apply_settings(self):

        instance = mayalib.find_render_instance()
        if not instance:
            return

        settings = mayalib.read_settings(instance)

        # Apply settings from node
        self.publish.setChecked(settings["suspendPublishJob"])
        self.priority_slider.setValue(settings["priority"])
        self.defaultlayer.setChecked(settings["includeDefaultRenderLayer"])
        self.run_slap_comp.setChecked(settings["runSlapComp"])

        if settings.get("flowFile", None):
            self.flow_file.setText(settings["flowFile"])

        white_list = "whiteList" in settings
        self.white_list.setChecked(white_list)
        self.black_list.setChecked(not white_list)

        self.listed_machines.addItems(settings["machineList"].split(" "))

    def _get_list_type(self):
        return self.white_list.isChecked

    def _get_listed_machines(self):
        # Turn unicode to strings
        return [str(self.listed_machines.item(r).text()) for r in
                range(self.listed_machines.count())]


def show(root=None, debug=False, parent=None):
    """Display Loader GUI

    Arguments:
        debug (bool, optional): Run loader in debug-mode,
            defaults to False

    """

    try:
        module.window.close()
        del module.window
    except (RuntimeError, AttributeError):
        pass

    if debug is True:
        io.install()

        any_project = next(
            project for project in io.projects()
            if project.get("active", True) is not False
        )

        api.Session["AVALON_PROJECT"] = any_project["name"]

    with tools_lib.application():
        window = App(parent)
        # Do not apply stylesheet, not nessecary in Maya
        # window.setStyleSheet(style.load_stylesheet())
        window.show()
        window.refresh()

        module.window = window
