const newProjectModal = new Modal(document.getElementById("new-project-modal"), {
    width: '400px',
    height: '400px',
    displayStyle: 'flex',
    classList: ['theme-modal-container']
})


function logout() {
    document.cookie.split(";").forEach(function(c) {
        document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
    });
    window.location.reload()
}



window.addEventListener('load', ()=>{
    const proj_container = document.getElementById("profile-projects")
    modFetch('/projects', 'GET').then(data => {
        for (const proj of data) {
            // console.log(proj)
            const div = document.createElement("div")
            div.classList.add('project', 'gen-btn')
            div.innerHTML = `
            <div>
                <b data-name="${proj.name}">${proj.name}</b>
                <span>${proj.descr}</span>
            </div>
            <div>
                <span>entry points: ${proj.entry_points}</span>
                <span>schedules: ${proj.schedules}</span>
                ${
                    (proj.schedules_enabled > 0) ?
                    `<span style="color:green;">enabled: ${proj.schedules_enabled}</span>` :
                    `<span style="color:grey;">enabled: 0</span>`
                }
            </div>
            `
            div.setAttribute('title', proj.descr)
            div.onclick = ()=>{
                window.location = `/project/${proj.name_hash}`
            }
            div.oncontextmenu = (ev)=>projectContextMenu(ev, proj.name, proj.name_hash)
            let touchTimeout = null
            div.addEventListener('touchstart', (ev)=>{
                ev.preventDefault()
                touchTimeout = setTimeout(()=>{
                    clearTimeout(touchTimeout)
                    touchTimeout = null
                    projectContextMenu(ev, proj.name, proj.name_hash)
                }, 1000)
            });
            div.addEventListener('touchend', (ev)=>{
                if (touchTimeout) {
                    clearTimeout(touchTimeout)
                    touchTimeout = null
                    div.click()
                }
            });

            proj_container.appendChild(div)
        }
    }).catch(err=>AlertModal.open(err))
})


function newProject() {
    const new_proj_box = document.getElementById("new-project-modal")
    const name = new_proj_box.querySelector("[name='project_name']").value.trim()
    const descr = new_proj_box.querySelector("[name='project_descr']").value.trim()

    modFetch("/projects/new", 'POST', {name, descr}).then(res=>{
        newProjectModal.close()
        // window.location = `/project/${res}`
        window.location.reload()
    }).catch(err=>AlertModal.open(err))
}


async function deleteProject(project_hash) {
    return modFetch(`/projects/delete`, 'POST', {project_hash})
}

async function renameProject(project_hash, new_name) {
    return modFetch(`/projects/rename`, 'POST', {project_hash, new_name})
}




function projectContextMenu(ev, name, hash) {
    ev.preventDefault();

    let menu = new ContextMenu(ev.pageX, ev.pageY)
    menu.addNewOption("Delete", ()=>{
        ConfirmModal.open(
            `Are you sure you want to delete '${name}'?`,
            ()=>{
                deleteProject(hash).then(()=>{
                    window.location.reload()
                })
            }
        )
        menu.close()
    })

    menu.addNewOption("Rename", ()=>{
        PromptModal.open("New Name:", name, (new_name)=>{
            renameProject(hash, new_name).then(()=>{
                // window.location.reload()
                const projcard_name = document.querySelector(`[data-name="${name}"]`)
                projcard_name.innerHTML = new_name
                projcard_name.setAttribute('data-name', new_name)
            })
        })
        menu.close()
    })
    menu.open()
}

