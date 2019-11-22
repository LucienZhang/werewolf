/*
 * @Author: Lucien Zhang
 * @Date:   2019-10-04 16:47:05
 * @Last Modified by:   Lucien Zhang
 * @Last Modified time: 2019-10-05 15:45:46
 */
document.querySelector("#game_form").onsubmit = function() {
    let msg = ""

    let victory_mode = $('#victoryModeGroup input[name="victoryMode"]:checked').val();
    if (victory_mode === 'kill_group') {
        victory_mode = '屠边';
    } else if (victory_mode === 'kill_all') {
        victory_mode = '屠城';
    }
    msg += '游戏模式为：' + victory_mode + '\n';

    let captain_mode = $('#captainModeGroup input[name="captainMode"]:checked').val();
    if (captain_mode === 'with_captain') {
        captain_mode = '有警长';
    } else if (captain_mode === 'without_captain') {
        captain_mode = '没有警长';
    }
    msg += '警长模式为：' + captain_mode + '\n';

    let witch_mode = $('#witchModeGroup input[name="witchMode"]:checked').val();
    if (witch_mode === 'can_save_self') {
        witch_mode = '全程可以自救';
    } else if (witch_mode === 'first_night_only') {
        witch_mode = '仅首夜可以自救';
    } else if (witch_mode === 'cannot_save_self') {
        witch_mode = '全程不可自救';
    }
    msg += '女巫模式为：' + witch_mode + '\n';

    let villager = $('#villager option:selected').val();
    let normal_wolf = $('#normal_wolf option:selected').val();

    let role_cnt = parseInt(villager) + parseInt(normal_wolf);
    let single_roles = "";

    $('input[name="single_roles"]:checked').each(function() {
        // console.log($(this).next());
        single_roles += $(this).next().text() + ' = 1\n';
        role_cnt += 1;
    });
    msg += '游戏总人数为：' + role_cnt.toString() + '人\n';
    msg += '普通村民 = ' + villager + '\n';
    msg += '普通狼人 = ' + normal_wolf + '\n';
    msg += single_roles;

    return confirm(msg)

    // if (document.querySelector('#confirm').value != document.querySelector('#password').value) {
    //     alert("两次输入的密码不一致!");
    //     return false;
    // }
};
