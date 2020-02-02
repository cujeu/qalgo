# config.py
class Config:
    CSV_DATA_DIR = ""
    OUTPUT_DIR = ""
    STRATEGY_DIR = ""

    def __init__(self):
        self.CSV_DATA_DIR = '/home/jun/proj/qalgo/qstest/data'
        self.OUTPUT_DIR = '/home/jun/proj/qalgo/qstest/out'
        self.STRATEGY_DIR = '/home/jun/proj/qalgo/qstest/res'
        #DATABASE_TABLES = ['tb_users', 'tb_groups']

    def get_csv_dir(self):
        return self.CSV_DATA_DIR

    def get_strategy_dir(self):
        return self.STRATEGY_DIR

    def get_output_dir(self):
        return self.OUTPUT_DIR

