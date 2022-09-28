// require is provided by loader.min.js.

require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.34.0/min/vs' }});
// require.config({ paths: { 'vs': 'https://unpkg.com/monaco-editor@latest/min/vs' }}); // slow :(

require(["vs/editor/editor.main"], () => {

    fetch('https://cdn.jsdelivr.net/npm/monaco-themes@0.4.1/themes/Monokai.json')
    .then(data => data.json())
    .then(data => {
        monaco.editor.defineTheme('monokai', data);
        monaco.editor.setTheme('monokai');
    })

    const editorElem = document.getElementById('editor')
    window.editor = monaco.editor.create(editorElem, {
        language: 'python',
        theme: 'vs-dark',
        fontSize: '12px',
        fontWeight: '400',
        automaticLayout: true,
    });

    window.editor.getModel().dispose() // remove default model

});



const AlertModal = new ModalAlert({
    css: {
        backgroundColor: 'rgb(39,40,34)',
        color: 'white',
    }
})


function openOutputWindow() {
    const outputElem = document.getElementById('output')
    outputElem.innerText = ''
    outputElem.parentElement.style.display = ''
    return outputElem
}

function closeOutputWindow() {
    document.querySelector('.output-container').style.display='none'
    window.editor.focus()
}



const RUN = () => {
    const outputElem = openOutputWindow()
    API.run().then(res=>{
        outputElem.innerText = res
    })
}


const folder_contextmenu = (ev, item) => {
    ev.preventDefault();
    let menu = new ContextMenu(ev.pageX, ev.pageY)

    menu.addNewOption("New File", ()=>{
        const name = prompt("File Name:")
        if (name) {
            API.newFile(item.path, name).then(res=>{
                console.log(res)
                TREE.newItem(res, item)
            }).catch(err=>AlertModal.open(err))
        }
        menu.close()
    })
    menu.addNewOption("New Folder", ()=>{
        const name = prompt("Folder Name:")
        if (name) {
            API.newFolder(item.path, name).then(res=>{
                console.log(res)
                TREE.newItem(res, item)
            }).catch(err=>AlertModal.open(err))
        }
        menu.close()
    })
    if (item.path && item.path!=="/") {
        menu.addNewOption("Delete", ()=>{
            if (confirm(`Are you sure you want to delete ${item.name}?`)) {
                API.deleteFolder(item.path).then(res=>{
                    TREE.deleteItem(item)
                }).catch(err=>AlertModal.open(err))
            }
            menu.close()
        })
    }
    menu.open()
};


const file_contextmenu = (ev, item) => {
    ev.preventDefault();
    let menu = new ContextMenu(ev.pageX, ev.pageY)

    menu.addNewOption("Rename", ()=>{
        console.log(item.name)
        menu.close()
    })
    menu.addNewOption("Delete", ()=>{
        if (confirm(`Are you sure you want to delete ${item.name}?`)) {
            API.deleteFile(item.path).then(res=>{
                if (item.model) {
                    item.model.dispose()
                }
                TREE.deleteItem(item)
            }).catch(err=>AlertModal.open(err))
        }
        menu.close()
    })
    menu.open()
};





window.addEventListener('load', (event) => {
    const editorElem = document.getElementById('editor')
    editorElem.addEventListener('keydown', (e)=>{
        if (e.key==='s' && e.ctrlKey === true) { // save file
            e.preventDefault();
            const path = editorElem.getAttribute('data-path')
            const src = window.editor.getValue()
            API.saveFile(path, src).then(res=>{
                const item = TREE.getItemFromPath(path)
                item.src = src
                TREE.markItemClean(item)
            }).catch(err=>AlertModal.open(err))
        }

        if (e.key==='b' && e.ctrlKey === true) { // run project
            e.preventDefault();
            RUN()
        }
    })

    TREE.setOptions({
        file_contextmenu,
        folder_contextmenu,
        onclick: (item)=>{
            if (item.type!=='folder') {
                if (item.path) {
                    editorElem.setAttribute('data-path', item.path)
                }

                if (!item.model)
                    item.model = monaco.editor.createModel(item.src, item.language)

                item.model.onDidChangeContent(evt=>{
                    TREE.markItemDirty(item)
                })
                window.editor.setModel(item.model)
            }
        }
    });

    API.loadTree(TREE)

})
