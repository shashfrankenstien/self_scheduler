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
    constructor(user, job) {
        this.user = user
        this.job = job
    }

    loadTree(treeObj) {
        modFetch(`/${this.user}/${this.job}/tree`, "GET").then(res=>{
            treeObj.showTree(res);
        }).catch(err=>{
            alert(err)
        })
    }

    newFile(path, name) {
        return modFetch(`/${this.user}/${this.job}/file/new`, "POST", {
            path,
            name
        }).then(res=>{
            return res
        })
    }

    saveFile(path, src) {
        console.log("save", path)
        return modFetch(`/${this.user}/${this.job}/file/save`, "POST", {path, src})
    }

    deleteFile(path) {
        console.log("delete", path)
        return modFetch(`/${this.user}/${this.job}/file/delete`, "POST", {
            path,
        }).then(res=>{
            return res
        })
    }

    run() {
        return modFetch(`/${this.user}/${this.job}/run`, "GET")
    }
}

