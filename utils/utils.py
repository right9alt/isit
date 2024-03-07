import logging

class Context:
  def __init__(self):
    self.db_handle = None
    self.logger = logging.getLogger(__name__)

  def set_logger_handler(self, curr_context):
    logging.basicConfig(level=logging.INFO)
    # Создание обработчика для записи в файл
    file_handler = logging.FileHandler(curr_context)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    self.logger.addHandler(file_handler)
