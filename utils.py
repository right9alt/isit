import logging

class Context:
  def __init__(self):
    self.db_handle = None
    self.logger = None
  
  
  def set_logger(self, curr_context):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Создание обработчика для записи в файл
    file_handler = logging.FileHandler(curr_context)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    self.logger = logger
