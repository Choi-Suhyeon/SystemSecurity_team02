import sys
from PyQt5.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

class TreeWidgetExample(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('QTreeWidget Example')
        self.resize(400, 300)

        # QTreeWidget 생성
        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)  # 열 개수 설정
        self.tree.setHeaderLabels(['Name', 'Value'])  # 헤더 설정

        # 루트 아이템 추가
        root = QTreeWidgetItem(self.tree)
        root.setText(0, 'Root Item')
        root.setText(1, 'Root Value')

        # 자식 아이템 추가
        child1 = QTreeWidgetItem(root)
        child1.setText(0, 'Child 1')
        # child1.setText(1, 'Value 1')

        child2 = QTreeWidgetItem(root)
        child2.setText(0, 'Child 2')
        child2.setText(1, 'Value 2')

        # 자식의 자식 아이템 추가
        grandchild = QTreeWidgetItem(child1)
        grandchild.setText(0, 'Grandchild 1')
        grandchild.setText(1, 'Value 1.1')

        # 트리 열기
        self.tree.expandAll()

        # 레이아웃 설정
        layout = QVBoxLayout()
        layout.addWidget(self.tree)
        self.setLayout(layout)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TreeWidgetExample()
    ex.show()
    sys.exit(app.exec_())

