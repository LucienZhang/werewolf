/*
 * @Author: Lucien Zhang
 * @Date:   2019-09-29 17:28:56
 * @Last Modified by:   Lucien Zhang
 * @Last Modified time: 2019-09-29 17:56:34
 */

(function(window) {
    var ajaxUtils = {};

    function getRequestObject() {
        if (window.XMLHttpRequest) {
            return (new XMLHttpRequest());
        } else if (window.ActiveXObject) {
            //For very old IE browsers
            return (new ActiveXObject("Microsoft.XMLHTTP"));

        } else {
            window.alert("Ajax is not supported!");
            return null;
        }
    }

    ajaxUtils.sendGetRequest =
        function(requestUrl, responseHandler) {
            let request = getRequestObject();
            request.onreadystatechange =
                function() {
                    handleResponse(request, responseHandler);
                };
            request.open("GET", requestUrl, true);
            request.send(null); //for POST only
        };

    function handleResponse(request, responseHandler) {
        if ((request.readyState == 4) && (request.status == 200)) {
            responseHandler(request);
        }
    }

    window.$ajaxUtils = ajaxUtils;

})(window);
