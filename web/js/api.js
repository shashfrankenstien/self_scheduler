const modFetch = async (endpoint, method, body) => {
    if (body) {
        body = JSON.stringify(body)
    }
    return fetch(endpoint, {
        method,
        headers: {'Content-Type': 'application/json'},
        credentials: "same-origin",
        body: body || null
    }).then(resp=>{
        return resp.json()
    }).then(rj=>{
        if (rj.success) {
            return rj.success
        } else {
            throw new Error(rj.error)
        }
    })
}



class SS_Project_API {
    constructor(project_name) {
        this.project_name = project_name
    }

    loadTree(treeObj) {
        modFetch(`/project/${this.project_name}/tree`, "GET").then(res=>{
            treeObj.showTree(res);
        }).catch(err=>{
            alert(err)
        })
    }

    newFile(path, name) {
        return modFetch(`/project/${this.project_name}/file/new`, "POST", {
            path,
            name
        }).then(res=>{
            return res
        })
    }

    saveFile(path, src) {
        console.log("save", path)
        return modFetch(`/project/${this.project_name}/file/save`, "POST", {path, src})
    }

    deleteFile(path) {
        console.log("delete", path)
        return modFetch(`/project/${this.project_name}/file/delete`, "POST", {
            path,
        }).then(res=>{
            return res
        })
    }

    run() {
        return modFetch(`/project/${this.project_name}/run`, "GET")
    }
}

