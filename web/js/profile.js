const newProjectModal = new Modal(document.getElementById("new-project-modal"), {
    width: '400px',
    height: '400px',
    displayStyle: 'flex',
    css: {
        backgroundColor: 'rgb(39,40,34)',
        color: 'white',
    }
})

window.addEventListener('load', ()=>{
    const proj_container = document.getElementById("profile-projects")

    modFetch('/projects', 'GET').then(data => {
        for (const proj of data) {
            console.log(proj)
            const div = document.createElement("div")
            div.classList.add('project')
            div.innerHTML = proj.name
            div.onclick = ()=>{
                window.location = `/project/${proj.name_hash}`
            }
            proj_container.appendChild(div)
        }
    }).catch(err=>AlertModal.open(err))
})



function logout() {
    document.cookie.split(";").forEach(function(c) {
        document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
    });
    window.location.reload()
}



function newProject() {
    const new_proj_box = document.getElementById("new-project-modal")
    const name = new_proj_box.querySelector("[name='project_name']").value.trim()
    const descr = new_proj_box.querySelector("[name='project_descr']").value.trim()
    modFetch("/project/new", 'POST', {name, descr}).then(res=>{
        newProjectModal.close()
        window.location = `/project/${res}`
    }).catch(err=>AlertModal.open(err))
}
