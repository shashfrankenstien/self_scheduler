

class FileTree {
    constructor(element, options) {
        this.element = element
        this.path_map = {}
        this.setOptions(options)
    }

    setOptions(options) {
        this.options = options || {}

        this.options.folderIcon = this.options.folderIcon || `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><!--! Font Awesome Free 6.1.1 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free (Icons: CC BY 4.0, Fonts: SIL OFL 1.1, Code: MIT License) Copyright 2022 Fonticons, Inc. --><path d="M464 96h-192l-64-64h-160C21.5 32 0 53.5 0 80V160h512V144C512 117.5 490.5 96 464 96zM0 432C0 458.5 21.5 480 48 480h416c26.5 0 48-21.5 48-48V192H0V432z"/></svg>`
        this.options.folderOpenIcon = this.options.folderOpenIcon || `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 576 512"><!--! Font Awesome Free 6.1.1 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free (Icons: CC BY 4.0, Fonts: SIL OFL 1.1, Code: MIT License) Copyright 2022 Fonticons, Inc. --><path d="M147.8 192H480V144C480 117.5 458.5 96 432 96h-160l-64-64h-160C21.49 32 0 53.49 0 80v328.4l90.54-181.1C101.4 205.6 123.4 192 147.8 192zM543.1 224H147.8C135.7 224 124.6 230.8 119.2 241.7L0 480h447.1c12.12 0 23.2-6.852 28.62-17.69l96-192C583.2 249 567.7 224 543.1 224z"/></svg>`
        this.options.fileIcon = this.options.fileIcon || `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-file-earmark-code" viewBox="0 0 16 16"> <path d="M14 4.5V14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h5.5L14 4.5zm-3 0A1.5 1.5 0 0 1 9.5 3V1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V4.5h-2z"/> <path d="M8.646 6.646a.5.5 0 0 1 .708 0l2 2a.5.5 0 0 1 0 .708l-2 2a.5.5 0 0 1-.708-.708L10.293 9 8.646 7.354a.5.5 0 0 1 0-.708zm-1.292 0a.5.5 0 0 0-.708 0l-2 2a.5.5 0 0 0 0 .708l2 2a.5.5 0 0 0 .708-.708L5.707 9l1.647-1.646a.5.5 0 0 0 0-.708z"/> </svg>`

        this.options.folder_contextmenu = this.options.folder_contextmenu || (()=>{})
        this.options.file_contextmenu = this.options.file_contextmenu || (()=>{})

        this.onclick = this.options.onclick || (()=>{})
        this.selected_item = null
    }

    getDisplay(item) {
        let start
        if (item.type=='folder') {
            let open_indicator = ""//(item.open) ? "-" : "+"
            let folderIcon = (this.options.folderIcon || "")
            folderIcon = (item.open) ? this.options.folderOpenIcon || folderIcon : folderIcon
            start = open_indicator + "&nbsp;" + folderIcon + "&nbsp;"
        } else {
            start = (this.options.fileIcon || "|") + "&nbsp;"
        }
        if (item.level >= 1) {
            return "&nbsp;".repeat(5 * item.level) + start +item.name
        } else {
            return start + item.name
        }
    }

    createNode(item, parent) {
        item.id = `${parent.id || "root"}-${item.name}`
        item.level = (parent.level + 1 || 0)

        let node = document.createElement('div')
        item.node = node
        node.id = item.id
        node.classList.add("file-tree-element")
        node.innerHTML = this.getDisplay(item)

        if (parent.open || item.type==='folder') {
            node.style.display = ''
        } else {
            node.style.display = 'none'
        }

        if (item.type==='folder'){
            item.node.addEventListener('contextmenu', (ev)=>this.options.folder_contextmenu(ev, item, this));
        } else {
            item.node.addEventListener('contextmenu', (ev)=>this.options.file_contextmenu(ev, item, this));
        }
        node.addEventListener('click', (ev) => {
            ev.preventDefault()
            this._clicked(item)
        })
        if (parent.node)
            parent.node.after(node)
        else
            this.element.appendChild(node)
        this.path_map[item.path] = item

        if (item.selected === true)
            this._clicked(item)

        return item
    }


    _showTree(data, parent) {
        parent = parent || {}
        for (const d of data) {
            let item = this.createNode(d, parent)
            if (d.type=="folder") {
                this._showTree(d.children || [], item)
            }
        }
    }

    showTree(data) {
        // this.data = data
        this.element.innerHTML = "" // delete existing tree
        this._showTree(data)
        setTimeout(()=>console.log(data), 500)
    }

    getItemFromPath(path) {
        return this.path_map[path]
    }

    _openFolder(item) {
        item.children.forEach(i=>{
            i.node.style.display = ''
            if (i.type==='folder' && i.open) {
                this._openFolder(i)
            }
        })
    }

    _closeFolder(item) {
        item.children.forEach(i=>{
            i.node.style.display = 'none'
            if (i.type==='folder' && i.open) {
                this._closeFolder(i)
            }
        })
    }

    _selectFile(item) {
        for (const p in this.path_map) {
            const d = this.path_map[p]
            if (d.type!='folder') {
                d.node.classList.remove('selected')
            }
        }

        item.node.classList.add('selected')
        item.selected = true
    }

    _clicked(item) {
        if (item.type==='folder') {
            if(item.open === true) {
                item.open = false
                this._closeFolder(item)
            } else {
                item.open = true
                this._openFolder(item)
            }

            item.node.innerHTML = this.getDisplay(item)
        } else {
            this._selectFile(item)
        }
        this.onclick(item)
    }


    // other operations

    markItemDirty(item) {
        if (item.dirty !== true) {
            item.dirty = true
            item.node.innerHTML = item.node.innerHTML + " *"
            item.node.classList.add('dirty')
        }
    }

    markItemClean(item) {
        if (item.dirty === true) {
            item.dirty = false

            item.node.classList.remove('dirty')
            let html = item.node.innerHTML
            if (html.endsWith("*"))
                item.node.innerHTML = html.substring(0, html.length - 2)
        }
    }

    delete(item) {
        item.node.remove()
        delete this.path_map[item.path]
    }

}
