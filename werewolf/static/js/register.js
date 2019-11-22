/*
 * @Author: Lucien Zhang
 * @Date:   2019-09-30 18:59:07
 * @Last Modified by:   Lucien Zhang
 * @Last Modified time: 2019-09-30 19:54:59
 */
document.querySelector("#user_form").onsubmit = function() {
    // if (document.querySelector('#username').value == "") {
    //     alert("用户名不能为空!");
    //     return false;
    // }
    // if (document.querySelector('#password').value == "") {
    //     alert("密码不能为空!");
    //     return false;
    // }
    if (document.querySelector('#confirm').value != document.querySelector('#password').value) {
        alert("两次输入的密码不一致!");
        return false;
    }
};
