import os
from flask import Flask

def create_app():
    # 获取当前文件所在目录的父目录作为项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 使用相对于项目根目录的路径设置模板和静态文件夹
    app = Flask(__name__, 
                template_folder=os.path.join(project_root, 'templates'),
                static_folder=os.path.join(project_root, 'static'))
    
    app.config['SECRET_KEY'] = '1qaz'
    
    # 注册蓝图 - 这是关键！
    from . import routes
    app.register_blueprint(routes.bp)
    
    return app