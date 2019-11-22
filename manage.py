# -*- coding: utf-8 -*-
# @Author: Lucien Zhang
# @Date:   2019-09-22 15:57:01
# @Last Modified by:   Lucien Zhang
# @Last Modified time: 2019-09-22 18:35:34

from werewolf import create_app

if __name__ == "__main__":
    # app = create_app('development')
    app = create_app()
    # print(app.root_path)
    # print(app.instance_path)
    app.run(port=app.config['PORT'])
