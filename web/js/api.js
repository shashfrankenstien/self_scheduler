
class SS_Project_API {
    constructor(project) {
        this.project = project
    }

    getProperties() {
        return modFetch(`/project/${this.project}/properties`, "GET").then(res=>{
            return res
        })
    }

    loadTree() {
        return modFetch(`/project/${this.project}/tree`, "GET")
    }

    newFile(path, name) {
        return modFetch(`/project/${this.project}/file/new`, "POST", {
            path,
            name
        })
    }

    fileSrc(path) {
        return modFetch(`/project/${this.project}/file/src`, "POST", {path})
    }


    saveFile(path, src) {
        console.log("save", path)
        return modFetch(`/project/${this.project}/file/save`, "POST", {path, src})
    }

    deleteFile(path) {
        console.log("delete", path)
        return modFetch(`/project/${this.project}/file/delete`, "POST", {
            path,
        })
    }

    newFolder(path, name) {
        return modFetch(`/project/${this.project}/folder/new`, "POST", {
            path,
            name
        })
    }

    deleteFolder(path) {
        return modFetch(`/project/${this.project}/folder/delete`, "POST", {
            path
        })
    }

    rename(path, name) {
        return modFetch(`/project/${this.project}/rename`, "POST", {
            path,
            name
        })
    }



    newEntryPoint(file, func, make_default) {
        return modFetch(`/project/${this.project}/entry-point/new`, "POST", {
            file,
            func,
            make_default
        })
    }

    deleteEntryPoint(epid) {
        return modFetch(`/project/${this.project}/entry-point/delete`, "POST", {epid})
    }


    runAsync(epid, msg_cb) {
        return streamFetch(`/project/${this.project}/run`, "POST", {epid}, msg_cb)
    }
}

