import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import pyqtgraph as pg

from task import Task, load_param, save_param


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.param = load_param('param.json')
        self.ustan_ui()
        
    def ustan_ui(self):
        self.setWindowTitle("Расчет")
        self.setGeometry(100, 100, 1300, 700)
        
        central = QWidget()
        self.setCentralWidget(central)
        position = QHBoxLayout(central)
        
        # Левая панель - параметры
        left = QWidget()
        left_position = QVBoxLayout(left)
        
        # Параметр A
        a_group = QGroupBox("Параметр A")
        a_position = QVBoxLayout(a_group)

        self.a_label = QLabel("a:")
        self.a_spin = QDoubleSpinBox()
        self.a_spin.setRange(1.0, 5.0)         
        self.a_spin.setSingleStep(0.1)          
        self.a_spin.setDecimals(1)              
        self.a_spin.setValue(self.param['a'])   
        self.a_spin.valueChanged.connect(self.change_a)

        a_position.addWidget(self.a_label)
        a_position.addWidget(self.a_spin)


        # Параметр B
        b_group = QGroupBox("Параметр B")
        b_position = QVBoxLayout(b_group)

        self.b_label = QLabel("b:")
        self.b_spin = QDoubleSpinBox()
        self.b_spin.setRange(1.0, 3.0)         
        self.b_spin.setSingleStep(0.1)         
        self.b_spin.setDecimals(1)              
        self.b_spin.setValue(self.param['b'])
        self.b_spin.valueChanged.connect(self.change_b)

        b_position.addWidget(self.b_label)
        b_position.addWidget(self.b_spin)

        
        # Кнопки
        self.run_btn = QPushButton("Выполнить расчет")
        self.run_btn.clicked.connect(self.run_calc)
        
        self.save_btn = QPushButton("Сохранить параметры")
        self.save_btn.clicked.connect(self.save_param)
        
        # Добавляем 
        left_position.addWidget(a_group)
        left_position.addWidget(b_group)
        left_position.addWidget(self.run_btn)
        left_position.addWidget(self.save_btn)
        left_position.addStretch()
        
        # Правая панель - график
        right = QWidget()
        right_position = QVBoxLayout(right)
        
        self.plot = pg.PlotWidget()
        self.plot.setBackground('white')
        self.line = self.plot.plot(pen='green')
        
        self.result = QLabel("Результат: -")
        
        right_position.addWidget(self.plot)
        right_position.addWidget(self.result)
        
        position.addWidget(left)
        position.addWidget(right)
        
    def change_a(self, value):
        self.param['a'] = value 
        self.a_label.setText(f"a: {self.param['a']:.1f}")
        self.plot_up()
        
    def change_b(self, value):
        self.param['b'] = value 
        self.b_label.setText(f"b: {self.param['b']:.1f}")
        self.plot_up()
        
    def plot_up(self):
        # предпросмотр
        task = Task(self.param)
        data = task.get_plot_data()
        self.line.setData(data['x'], data['y'])
        
    def run_calc(self):
        self.run_btn.setEnabled(False)
        self.result.setText("Идёт расчет...")

        # Создаем рабочий поток
        self.worker = Worker(self.param)
        self.worker.finished.connect(self.calc_finished)
        self.worker.start()

    def calc_finished(self, result):
        self.run_btn.setEnabled(True)
        self.result.setText(f"Результат: {result}")
        
        # Обновляем график
        task = Task(self.param)
        data = task.get_plot_data()
        self. line.setData(data['x'], data['y'])
        
    def save_param(self):
        save_param(self.param, 'param.json')
        QMessageBox.information(self, "Сохранение", "Параметры сохранены!")
        
    def load_param(self):
        self.param = load_param('param.json')
        self.a_spin.setValue(float(self.param['a']))
        self.b_spin.setValue(float(self.param['b']))
        self.plot_up()
        QMessageBox.information(self, "Обновление", "Параметры обновлены!")


class Worker(QThread):
    finished = pyqtSignal(object)
    
    def __init__(self, param):
        super().__init__()
        self.param = param
        
    def run(self):
        task = Task(self.param)
        result = task.solve()  
        self.finished.emit(result)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
