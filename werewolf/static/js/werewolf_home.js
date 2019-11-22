/*
 * @Author: Lucien Zhang
 * @Date:   2019-09-28 17:28:24
 * @Last Modified by:   Lucien Zhang
 * @Last Modified time: 2019-10-06 22:02:04
 */

document.querySelector("#setup").onclick = function() { location.href = '/werewolf/setup' };
document.querySelector("#join").onclick = function() {
    let gid = prompt("请输入房间号");
    let re = /^[1-9]\d*$/;
    if (gid != null && gid != "" && re.test(gid)) {
        location.href = '/werewolf/join?gid=' + gid
    }
};


// document.querySelector("#setup").onclick = function() { location.href = "{{ url_for('setup') }}" };
