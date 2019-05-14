function like(div) {
    const url = '/api/like/set';
    const request = new XMLHttpRequest();
    const array = div.id.split(';');
    const img = document.getElementById(div.id + ';img');
    const text = document.getElementById(div.id + ';text');
    request.open("POST", url, true);
    request.setRequestHeader('Content-Type', 'application/json');
    request.onreadystatechange = function () {
        if (request.readyState == XMLHttpRequest.DONE) {
            const result = JSON.parse(request.responseText);
            if ('Like already placed!' === result['result']) {
                const request_remove = new XMLHttpRequest();
                request_remove.open("POST", '/api/like/remove', true);
                request_remove.setRequestHeader('Content-Type', 'application/json');
                request_remove.send(JSON.stringify({
                    'author': array[1],
                    'peer_id': array[0]
                }));
                img.src = "../static/img/non-like.png";
                if (result['count'] - 1 != 0) {
                    text.innerHTML = result['count'] - 1;
                }
                else {
                    text.innerHTML = '';
                }
                text.className = "text-capitalize h3";
            }
            else if ('Success!' === result['result']) {
                img.src = "../static/img/like.png";
                if (result['count'] + 1 != 0) {
                    text.innerHTML = result['count'] + 1;
                }
                else {
                    text.innerHTML = '';
                }
                text.className = "text-danger h3";
            }
        }
    };

    request.send(JSON.stringify({
        'author': array[1],
        'peer_id': array[0]
    }));

}