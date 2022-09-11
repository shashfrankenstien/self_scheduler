// require is provided by loader.min.js.
require.config({ paths: { 'vs': 'https://unpkg.com/monaco-editor@latest/min/vs' }});
require(["vs/editor/editor.main"], () => {

    fetch('https://cdn.jsdelivr.net/npm/monaco-themes@0.4.1/themes/Monokai.json')
    .then(data => data.json())
    .then(data => {
        monaco.editor.defineTheme('monokai', data);
        monaco.editor.setTheme('monokai');
    })

    const editorElem = document.getElementById('editor')
    window.editor = monaco.editor.create(editorElem, {
        // language: 'python',
        theme: 'vs-dark',
        fontSize: '11px',
        fontWeight: '400',
        automaticLayout: true,
    });

});


const folder_contextmenu = (ev, item, treeObj) => {
    ev.preventDefault();
    let menu = new ContextMenu(ev.pageX, ev.pageY)

    menu.addNewOption("New File", ()=>{
        const name = prompt("File Name:")
        API.newFile(item.path, name).then(struct=>{
            treeObj.showTree(struct)
        })
        menu.close()
    })
    menu.addNewOption("New Folder", ()=>{
        console.log(item.path)
        menu.close()
    })
    if (item.path && item.path!=="/") {
        menu.addNewOption("Delete", ()=>{
            console.log(item.path)
            menu.close()
        })
    }
    menu.open()
};


const file_contextmenu = (ev, item, treeObj) => {
    ev.preventDefault();
    let menu = new ContextMenu(ev.pageX, ev.pageY)

    menu.addNewOption("Rename", ()=>{
        console.log(item.name)
        menu.close()
    })
    menu.addNewOption("Delete", ()=>{
        API.deleteFile(item.path).then(struct=>{
            treeObj.showTree(struct)
        })
        menu.close()
    })
    menu.open()
};



const RUN = () => {
    const outputElem = document.getElementById('output')
    outputElem.innerText = ''
    outputElem.parentElement.style.display = ''
    API.run().then(res=>{
        outputElem.innerText = res
    })
}

window.addEventListener('load', (event) => {
    const editorElem = document.getElementById('editor')
    editorElem.addEventListener('keydown', (e)=>{
        if (e.key==='s' && e.ctrlKey === true) {
            e.preventDefault();
            const path = editorElem.getAttribute('data-path')
            const src = window.editor.getValue()
            API.saveFile(path, src).then(res=>{
                TREE.resetSrc(path, src)
            })
        }

        if (e.key==='b' && e.ctrlKey === true) {
            e.preventDefault();
            RUN()
        }
    })

    TREE.setOptions({
        // navigate: true, // allow navigate with ArrowUp and ArrowDown
        file_contextmenu,
        folder_contextmenu,
        onclick: (item)=>{
            if (item.type!=='folder') {
                const model = window.editor.getModel()
                model.setValue(item.src)
                model.tree_item = item
                monaco.editor.setModelLanguage(model, "python")
                if (item.path) {
                    editorElem.setAttribute('data-path', item.path)
                }
            }
        }
    });

    API.loadTree(TREE)

})
