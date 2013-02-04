// Thanks to David Chambers: davidchambersdesign.com
// Can't believe this isn't in the stdlib.
function makeSafe(text) {
  return text.replace(/[&<>"'`]/g, function (chr) {
    return '&#' + chr.charCodeAt(0) + ';';
  });
};

function handleFileSelect(evt) {
    var reader = new FileReader(),
        file = evt.target.files[0];

    reader.onload = readFile;
    reader.readAsText(file);
}

function readFile(evt) {
    data = JSON.parse(evt.target.result);
    console.log(data);
    data.entities.forEach(createEntity);
}

function createEntity(ent) {
    var dropzone = document.getElementById('entities'),
        entNode = document.createElement('li'),
        aspectsNode = document.createElement('li'),
        aspectNode, key;

    entNode.setAttribute('class', 'entity');
    entNode.innerHTML = '<b>' + makeSafe(ent.name) + '</b><br />' + makeSafe(ent.desc);

    if(ent.aspects) {
        aspectsNode.setAttribute('aspects');

        for (key in ent.aspects) {
            if (ent.aspects.hasOwnProperty(key)) {
                aspectNode = document.createElement('li');
                aspectNode.setAttribute('class', 'aspect');
                aspectNode.innerHTML = '<i>' + key + '</i>';
                aspectsNode.appendChild(aspectNode);
            }
        }

        entNode.appendChild(aspectsNode);
    }

    dropzone.appendChild(entNode);
}

document.getElementById('file').addEventListener('change', handleFileSelect, false);
