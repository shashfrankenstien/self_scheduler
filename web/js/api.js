
class SS_Project_API {
    constructor(project) {
        this.project = project
    }

    getProperties() {
        return modFetch(`/project/${this.project}/properties`, "GET").then(res=>{
            return res
        })
    }

    loadTree(treeObj) {
        return modFetch(`/project/${this.project}/tree`, "GET").then(res=>{
            treeObj.showTree(res);
        })
    }

    newFile(path, name) {
        return modFetch(`/project/${this.project}/file/new`, "POST", {
            path,
            name
        }).then(res=>{
            return res
        })
    }

    saveFile(path, src) {
        console.log("save", path)
        return modFetch(`/project/${this.project}/file/save`, "POST", {path, src})
    }

    deleteFile(path) {
        console.log("delete", path)
        return modFetch(`/project/${this.project}/file/delete`, "POST", {
            path,
        }).then(res=>{
            return res
        })
    }

    newFolder(path, name) {
        return modFetch(`/project/${this.project}/folder/new`, "POST", {
            path,
            name
        }).then(res=>{
            return res
        })
    }

    deleteFolder(path) {
        return modFetch(`/project/${this.project}/folder/delete`, "POST", {
            path
        }).then(res=>{
            return res
        })
    }

    rename(path, name) {
        return modFetch(`/project/${this.project}/rename`, "POST", {
            path,
            name
        }).then(res=>{
            return res
        })
    }

    runAsync(msg_cb) {
        return streamFetch(`/project/${this.project}/run`, "GET", null, msg_cb)
    }
}

