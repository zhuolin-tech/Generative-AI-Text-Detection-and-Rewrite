import logging
from forms.form_main import MainForm
from forms.form_user import UserForm
import json
from toolkit import InputProcessing, CustomJSONEncoder, LoggerManager
from external_api import DocumentProcess
import os
from tika import parser
from werkzeug.utils import secure_filename
import ahocorasick

class MainService:
    def __init__(self):
        # 导入文档处理接口
        self.document_process = DocumentProcess()
        # 导入输入处理模块
        self.input_processing = InputProcessing()
        # 导入主表单模块
        self.main_form = MainForm()
        # 导入用户表单模块
        self.user_form = UserForm()

        # 配置日志管理器
        logging.basicConfig(filename='logs/services.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.services_logger = LoggerManager('services_logger', 'logs/services.log').get_logger()  # 创建日志对象

    def process_humanized_text(self, user_id, origin_text, mode):
        """
        Process user input text and return rewriting results
        Input parameters:
           - user_id: User ID
           - origin_text: Original text input by user
           - mode: Rewriting mode
        Output parameters:
           - Returns rewriting results and HTTP status code
           - HTTP status codes: 200 for success, 400 for parameter errors (including non-existent user, word count less than 20, insufficient balance), 500 for internal errors
        """
        # ####### Data Processing Section #####################
        word_count = self.input_processing.word_count(origin_text)  # Calculate word count
        spend = self.input_processing.humanized_spend(word_count, mode)  # Calculate rewriting cost
        current_time = self.input_processing.get_current_time()  # Get current time

        # Set text processing type
        humanized_type = 'normal'  # Default to normal rewriting
        task = 'humanized'  # Default to rewriting task

        # ####### Data Validation Section #####################

        # Check if parameters are empty
        if not origin_text or not mode or not user_id:
            return {"error": "valid input are required"}, 400

        # Check if user ID exists
        if not self.user_form.check_user_id_exists(user_id):
            return {"error": "user_id is not exists"}, 400

        # Check if word count is less than 20
        if word_count <= 20:
            return {"error": "Word count less than 20"}, 400

        # Check if balance is sufficient
        if spend > self.main_form.get_balance(user_id):
            return {"error": "Insufficient balance"}, 400

        # Check if mode is valid
        if mode not in ['easy', 'medium', 'aggressive']:
            return {"error": "mode is not correct"}, 400

        # ####### Main Form Query and Logic Processing Section #####################
        try:
            # Get API balance before call
            balance_api_before = self.document_process.get_balance().get('balance')
            # Call API for text rewriting
            humanized_text_response = self.document_process.trans_to_human(origin_text, mode)
            # Get API balance after call
            balance_api_after = self.document_process.get_balance().get('balance')
            # Calculate API usage cost
            api_token_spend = balance_api_before - balance_api_after

            # If API cost is 0, use word count as cost
            if api_token_spend == 0:
                api_token_spend = word_count

            session = self.main_form.Session()
            try:
                # Insert records into humanized_history, spend_history, and api_usage tables
                if not self.main_form.add_humanized_history(session, user_id, current_time, origin_text, json.dumps(humanized_text_response), word_count, humanized_type):
                    raise Exception("Database insert humanized history failed")
                if not self.main_form.add_spend_history(session, user_id, current_time, spend, task):
                    raise Exception("Database insert spend history failed")
                if not self.main_form.add_api_history(session, user_id, current_time, task, api_token_spend, balance_api_after):
                    raise Exception("Database insert api usage failed")
                session.commit()

            except Exception as e:
                print(f"Internal Server Error: {e}")
                session.rollback()  # Rollback
                raise e  # Raise exception for logging and return 500 status code
            finally:
                session.close()

            return humanized_text_response, 200  # Success, return rewriting results

        # ####### Exception Handling Section #####################
        except Exception as e:
            self.services_logger.error(f"Internal Server Error: {e}")
            return {"error": "Internal Server Error"}, 500

    def process_humanize_chunks(self, user_id, origin_text, chunks, mode):
        """
        Process user input text and return rewriting results for chunks
        Input parameters:
           - user_id: User ID
           - origin_text: Original text input by user
           - chunks: List of text chunks
           - mode: Rewriting mode
        Output parameters:
           - humanized_chunks: Array of rewritten text segments for marking
           - humanized_text: Complete rewritten text
           - HTTP status codes: 200 for success, 400 for parameter errors (including non-existent user, word count less than 20, insufficient balance), 500 for internal errors
        """
        # ####### Data Processing Section #####################
        word_count = self.input_processing.word_count(origin_text)  # Calculate word count
        spend = self.input_processing.humanized_spend(word_count, mode)  # Calculate rewriting cost
        current_time = self.input_processing.get_current_time()  # Get current time

        merge_chunks = self.input_processing.merge_chunks(origin_text, chunks)  # Merge text chunks
        merge_chunks = self.input_processing.clean_chunks(merge_chunks)  # Clean text chunks
        outside_chunks = self.input_processing.find_outside_chunks(origin_text, merge_chunks)  # Mark text chunks

        # Set text processing type
        humanized_type = 'normal'
        task = 'humanized'   # Default to rewriting task

        # ####### Data Validation Section #####################

        # Check if parameters are empty
        if not origin_text or not mode or not user_id:
            return {"error": "valid input are required"}, 400

        # Check if user ID exists
        if not self.user_form.check_user_id_exists(user_id):
            return {"error": "user_id is not exists"}, 400

        # Check if word count is less than 20
        if word_count <= 20:
            return {"error": "Word count less than 20"}, 400

        # Check if balance is sufficient
        if spend > self.main_form.get_balance(user_id):
            return {"error": "Insufficient balance"}, 400

        # Check if mode is valid
        if mode not in ['easy', 'medium', 'aggressive']:
            return {"error": "mode is not correct"}, 400

        # ####### Main Form Query and Logic Processing Section #####################
        try:
            # Get API balance before call
            balance_api_before = self.document_process.get_balance().get('balance')
            # Call API for text rewriting
            humanize_merge_chunks_response = self.document_process.trans_to_human_list(merge_chunks, mode)
            # Extract output string list
            humanize_merge_chunks = humanize_merge_chunks_response.get("output_list", [])  # Extract output string list
            # Get API balance after call
            balance_api_after = self.document_process.get_balance().get('balance')
            # Calculate API usage cost
            api_token_spend = balance_api_before - balance_api_after
            # Combine text chunks and marked chunks
            humanized_text = self.input_processing.combine_chunks(origin_text, outside_chunks, humanize_merge_chunks, merge_chunks)
            # Serialize response
            humanized_text_response = {"text": humanized_text, "chunks": humanize_merge_chunks}

            # If API cost is 0, use word count as cost
            if api_token_spend == 0:
                api_token_spend = word_count

            session = self.main_form.Session()
            try:
                # 将记录写入humanized_history表和spend_history表以及api_usage表
                if not self.main_form.add_humanized_history(session, user_id, current_time, origin_text, json.dumps(humanized_text_response), word_count, humanized_type):
                    raise Exception("Database insert humanized history failed")
                if not self.main_form.add_spend_history(session, user_id, current_time, spend, task):
                    raise Exception("Database insert spend history failed")
                if not self.main_form.add_api_history(session, user_id, current_time, task, api_token_spend, balance_api_after):
                    raise Exception("Database insert api usage failed")
                session.commit()


            except Exception as e:
                print(f"Internal Server Error: {e}")
                session.rollback()  # 回滚
                raise e  # 抛出异常 并且在日志记录同时http状态码500返回
            finally:
                session.close()

            return humanized_text_response, 200  # 成功 返回降重结果 200

        # ####### 异常处理部分 #####################
        except Exception as e:
            self.services_logger.error(f"Internal Server Error: {e}")
            return {"error": "Internal Server Error"}, 500



    def process_check_text(self, user_id, origin_text):
        """
        Process user input text and return detection results
        Input parameters:
           - user_id: User ID
           - origin_text: Original text input by user
        Output parameters:
           - Returns detection results and HTTP status code
           - HTTP status codes: 200 for success, 400 for parameter errors, 401 for non-existent user, 402 for word count less than 20, 403 for insufficient balance, 500 for internal errors
        """

        # ####### Data Processing Section #####################
        word_count = self.input_processing.word_count(origin_text)  # Calculate word count
        spend = self.input_processing.check_spend(word_count)  # Calculate detection cost
        current_time = self.input_processing.get_current_time()  # Get current time

        # Set text processing type
        check_type = 'normal'  # Default to normal detection
        task = 'check'  # Default to detection task
        # ####### Data Validation Section #####################

        # Check if parameters are empty
        if not origin_text or not user_id:
            return {"error": "valid input are required"}, 400

        # Check if user ID exists
        if not self.user_form.check_user_id_exists(user_id):
            return {"error": "user_id is not exists"}, 400

        # Check if word count is less than 20
        if word_count <= 20:
            return {"error": "Word count less than 20"}, 400

        # Check if balance is sufficient
        if spend > self.main_form.get_balance(user_id):
            return {"error": "Insufficient balance"}, 400

        # ####### Main Form Query and Logic Processing Section ##########
        try:
            # Get API balance before call
            balance_api_before = self.document_process.get_balance().get('balance')
            # Call API for detection
            detection_text_response = self.document_process.ai_detection(origin_text)
            # Get API balance after call
            balance_api_after = self.document_process.get_balance().get('balance')
            # Calculate API usage cost
            api_token_spend = balance_api_before - balance_api_after

            session = self.main_form.Session()
            try:
                # Insert records into check_history, spend_history, and api_usage tables
                if not self.main_form.add_check_history(session, user_id, current_time, origin_text, json.dumps(detection_text_response), word_count, check_type):
                    raise Exception("Database insert humanized history failed")
                if not self.main_form.add_spend_history(session, user_id, current_time, spend, task):
                    raise Exception("Database insert spend history failed")
                if not self.main_form.add_api_history(session, user_id, current_time, task, api_token_spend, balance_api_after):
                    raise Exception("Database insert api usage failed")
                session.commit()

            except Exception as e:
                session.rollback()  # Rollback
                raise e  # Raise exception for logging and return 500 status code
            finally:
                session.close()

            return detection_text_response, 200  # Success, return detection results

        # ####### Exception Handling Section #####################
        except Exception as e:
            self.services_logger.error(f"Internal Server Error: {e}")
            return {"error": "Internal Server Error"}, 500


    def get_history(self, user_id, history_type):
        """
        Get user's history records
        Input parameters:
           - user_id: User ID
           - history_type: History record type, including spend_history, recharge_history, api_history
        Output parameters:
           - Returns history records and HTTP status code
           - HTTP status codes: 200 for success, 400 for parameter errors (including non-existent user, invalid history type), 500 for internal errors
        """

        # ####### Data Processing Section #####################

        # ####### Data Validation Section #####################
        # Check if parameters are empty
        if not user_id:
            return {"error": "valid input are required"}, 400

        # Check if user ID exists
        if not self.user_form.check_user_id_exists(user_id):
            return {"error": "user_id is not exists"}, 400

        # Check if history type is valid
        if history_type not in ['spend_history', 'recharge_history', 'api_history']:
            return {"error": "history_type is not correct"}, 400

        # ####### Main Form Query and Logic Processing Section ##########
        try:
            # Get history records
            history_list = self.main_form.get_history(user_id, history_type)
            # Serialize history records
            serialized_history = [self.input_processing.serialize(history) for history in history_list]
            return serialized_history, 200  # Success, return history records

        # ####### Exception Handling Section ##########
        except Exception as e:
            self.services_logger.error(f"Internal Server Error: {e}")
            return {"error": "Internal Server Error"}, 500

    def get_history_with_spend(self, user_id, history_type):
        """
        Get user's history records with spending details
        Input parameters:
           - user_id: User ID
           - history_type: History record type, including humanized_history, check_history
        Output parameters:
           - Returns history records and HTTP status code
           - HTTP status codes: 200 for success, 400 for parameter errors (including non-existent user, invalid history type), 500 for internal errors
        """

        # ####### 数据处理部分 #####################

        # ####### 数据检验部分 #####################
        # 检查参数是否为空值
        if not user_id:
            return {"error": "valid input are required"}, 400

        # 检查用户id是否存在
        if not self.user_form.check_user_id_exists(user_id):
            return {"error": "user_id is not exists"}, 400

        # 检查历史记录类型是否正确
        if history_type not in ['humanized_history', 'check_history']:
            return {"error": "history_type is not correct"}, 400

        # ####### 主表单查询部分以及逻辑处理 ##########
        try:
            # 获取历史记录
            history_list = self.main_form.get_history_with_spend(user_id, history_type)
            # 序列化历史记录
            result_list = self.input_processing.convert_result_to_dict_list(history_list, history_type)
            # 将序列化历史记录结果转换为json字符串
            history_list = json.dumps(result_list, cls=CustomJSONEncoder) if result_list else json.dumps([])

            return history_list, 200  # 成功 返回历史记录 200

        # ####### 异常处理部分 ##########
        except Exception as e:
            print(f"Internal Server Error: {e}")
            self.services_logger.error(f"Internal Server Error: {e}")
            return {"error": "Internal Server Error"}, 500

    def process_recharge(self, user_id, amount, amount_type, recharge_credit, recharge_type):
        """
        Process user recharge request
        Input parameters:
           - user_id: User ID
           - amount: Recharge amount
           - amount_type: Currency type, including USD, RMB
           - recharge_credit: Credit points received
           - recharge_type: Recharge type, including normal, free (promotional)
        Output parameters:
           - Returns recharge result and HTTP status code
           - HTTP status codes: 200 for success, 400 for parameter errors (including non-existent user, invalid currency type, invalid recharge type), 500 for internal errors
        """

        # ####### Data Processing Section #####################

        current_time = self.input_processing.get_current_time()

        # ####### Data Validation Section #####################
        # TODO Need to implement more validation checks
        # Check if parameters are empty
        if not user_id or not amount or not amount_type or not recharge_credit or not recharge_type:
            return {"error": "valid input are required"}, 400

        # Check if user ID exists
        if not self.user_form.check_user_id_exists(user_id):
            return {"error": "user_id is not exists"}, 400


        # ####### 主表单查询部分以及逻辑处理 ##########
        session = self.main_form.Session()
        try:
            if not self.main_form.add_recharge_history(session, user_id, current_time, amount, amount_type, recharge_credit, recharge_type):
                raise Exception("Database insert recharge history failed")
            return {"user_id": user_id, "message": "recharge success"}, 200

        # ####### 异常处理部分 ##################
        except Exception as e:
            self.services_logger.error(f"Internal Server Error: {e}")
            return {"error": "Internal Server Error"}, 500
        finally:
            session.close()

    def get_balance(self, user_id):
        """
        Get user's balance
        Input parameters:
           - user_id: User ID
        Output parameters:
           - Returns balance and user ID with HTTP status code
           - HTTP status codes: 200 for success, 400 for parameter errors (including non-existent user), 500 for internal errors
        """
        # ####### Data Processing Section ##################


        # ####### Data Validation Section ################
        # Check if parameters are empty
        if not user_id:
            return {"error": "valid input are required"}, 400

        # Check if user ID exists
        if not self.user_form.check_user_id_exists(user_id):
            return {"error": "user_id is not exists"}, 400

        # ####### Main Form Query and Logic Processing Section #############
        try:
            balance = self.main_form.get_balance(user_id)
            return {"user_id": user_id, "balance": balance}, 200  # Success, return balance

        # ####### Exception Handling Section ######################
        except Exception as e:
            self.services_logger.error(f"Internal Server Error: {e}")
            return {"error": "Internal Server Error"}, 500


    # File processing function
    def process_file(file):

        # Configure upload folder
        UPLOAD_FOLDER = 'uploads/'
        ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

        # Check if file type is allowed
        def allowed_file(filename):
            return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

        # Use Tika to parse file and extract text
        def extract_text_from_file(file_path):
            parsed = parser.from_file(file_path)
            return parsed.get('content', '')

        try:
            # Validate file extension
            if not allowed_file(file.filename):
                return {"error": "File type not allowed"}, 400

            # Safely save file to specified path
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)

            # Use Tika to extract text content from file
            extracted_text = extract_text_from_file(file_path)

            # Delete saved file
            os.remove(file_path)

            # Return filename and extracted text
            return {"filename": filename, "extracted_text": extracted_text}, 200

        except Exception as e:
            # Handle exception and return error message
            return {"error": str(e)}, 500

    def process_sensitive_words(self, origin_text):
        """
        Process sensitive word detection request
        Input parameters:
           - sensitive_words: List of sensitive words
        Output parameters:
           - Returns detection results and HTTP status code
           - HTTP status codes: 200 for success, 400 for parameter errors, 500 for internal errors
        """
        # ####### Data Processing Section ##################

        word_count = self.input_processing.word_count(origin_text)  # Calculate word count

        # 1. List of forbidden words and phrases
        FORBIDDEN_WORDS = [
            "Taiwan independence", "Free Taiwan", "Hong Kong independence", "Free Hong Kong",
            "Tibet independence", "Free Tibet", "Xinjiang independence", "Free Xinjiang",
            "Hu Jintao", "Wen Jiabao", "Falun Gong", "1989 Democracy Movement", "June 4 Movement",
            "Truthfulness, Compassion, Forbearance", "New Tang Dynasty", "Li Hongzhi",
            "Overthrow the Communist Party", "CCP Tyranny", "Turkic Revolution", "Wuer Kaixi",
            "CCP step down", "June 4th Student Movement", "1989 Student Movement",
            "June 9th Student Movement", "Renji Wangmo", "Rehabilitation of June 4th",
            "One-party dictatorship", "Down with the CCP", "Down with the Communist Party",
            "Voice of America", "Overthrow the CCP", "Tiananmen Lovers", "Eliminate the Communist Party",
            "China Liberal Party", "Li Keqiang takes over", "CCP", "Tiananmen", "Lama",
            "Dalai Lama", "Li Sharp", "Li Peng", "Save Diaoyu Islands", "Communist bandits",
            "Gao Qinrong", "Communist Party", "Wang Zhaoguo", "Zhu Rongji", "Jia Qinglin",
            "Great Prophecy", "Zeng Qinghong", "Ling Jihua", "Liu Yandong", "Zhang Dejiang",
            "17th National Congress", "Mao Zedong", "Marx", "Quit the Communist Party",
            "Wu Guanzheng", "Li Changchun", "Peng Liyuan", "Yu Zhengsheng", "Guo Boxiong",
            "Zhou Yongkang", "Chen Liangyu", "Hua Guofeng", "Deng Xiaoping", "Xi Jinping",
            "Li Yuanchao", "Li Keqiang", "Zhongnanhai", "He Guoqiang", "Jiang Zemin",
            "Song Zuying", "Ma Zhipeng", "Open letter", "18th National Congress", "Quran",
            "General Secretary", "Secretary Hu", "Muslims", "Press Office", "Diaoyu Islands",
            "Power Distribution Bureau", "Communism", "Epoch Times", "Hui Muslim riots",
            "Jiang Zehui", "Jiang Qing", "Lee Teng-hui", "Muxidi", "Taiwanese Nationalist Movement",
            "Taiwan Youth Independence League", "Taiwan Political Forum", "Taiwan Freedom League",
            "Tiananmen videotapes", "Tiananmen incident", "Tiananmen massacre", "Wang Baosen",
            "Wang Bingzhang", "Wang Ce", "Wang Chaohua", "Wang Dan", "Wang Fuchen", "Wang Gang",
            "Wang Hanwan", "Wang Huning", "Wang Juntao", "Wang Lixiong", "Wang Ruilin",
            "Wang Runsheng", "Wang Ruowang", "Wang Xizhe", "Wang Xiuli", "Wang Yeping",
            "Wei Jianxing", "Wei Jingsheng", "Wei Xinsheng", "Wen Yuankai", "Cultural Revolution",
            "Wu Baiyi", "Wu Bangguo", "Wu Fangcheng", "Wu Guanzheng", "Wu Hongda", "Wu Renhua",
            "Wu Xuecan", "Wuerkaixi", "Xu Bangqin", "Xu Caihou", "Xu Kuangdi", "Xu Shuiliang",
            "Dissident", "Yan Jiaqi", "Yan Mingfu", "Zhao Pinlu", "Zhao Xiaowei", "Zhao Ziyang",
            "Democratic Progressive Party", "Tiananmen Massacre", "Literary Inquisition",
            "Genocide", "Gerontocracy", "Free Asia", "Tibetan Government-in-Exile",
            "Great Prophecy", "Zeng Qinghong", "Ling Jihua", "Liu Yandong", "Zhang Dejiang"
        ]

        # 2. 构建 Aho-Corasick 自动机
        def build_ac_automaton(words):
            automaton = ahocorasick.Automaton()
            for index, word in enumerate(words):
                automaton.add_word(word, (index, word))
            automaton.make_automaton()
            return automaton

        # 初始化自动机
        automaton = build_ac_automaton(FORBIDDEN_WORDS)

        # ####### 数据检验部分 ################

        # 检查参数是否为空值
        if not origin_text:
            return {"error": "valid input are required"}, 400

        # 或者单词个数是否小于20
        if word_count <= 20:
            return {"error": "Word count less than 20"}, 400


        # ####### 主表单查询部分以及逻辑处理 #############
        try:
            # 4. 使用 Aho-Corasick 进行文本检测
            for _, (_, word) in automaton.iter(origin_text):
                return {"result": False, "message": f"Found forbidden word: {word}"}, 200

            # 5. 未检测到敏感词，返回成功
            return {"result": True, "message": "No forbidden word found"}, 200

        # ####### 异常处理部分 ######################
        except Exception as e:
            self.services_logger.error(f"Internal Server Error: {e}")
            return {"error": "Internal Server Error"}, 500

