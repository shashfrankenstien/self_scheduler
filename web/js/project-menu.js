
// try ModalDrawerRight
const projectPropsModal = new Modal(document.getElementById("project-props-modal"), {
    width: '700px',
    height: '500px',
    displayStyle: 'flex',
    classList: ['theme-modal-container'],
    transitionStartPos: {top:'30%', left: '-30%'},
    autoClose: true,
    noCloseBtn: true,
    afterClose: ()=>{
        if (window.editor) window.editor.focus()
    }
})


const newEntryPointModal = new Modal(document.getElementById("new-entry-point-modal"), {
    width: '350px',
    height: '280px',
    displayStyle: 'flex',
    classList: ['theme-modal-container'],
})

const newSchedModal = new Modal(document.getElementById("new-schedule-modal"), {
    width: '350px',
    height: '325px',
    displayStyle: 'flex',
    classList: ['theme-modal-container'],
})



const RUN_EP = (epid) => {
    projectPropsModal.close()
    RUN(epid)
}


const displayEntryPoints = (eps, epElem) => {
    epElem = epElem || document.getElementById("entry-points")
    if(epElem) {
        epElem.innerHTML = ""

        for (const ep of eps) {
            const container = document.createElement("div")
            container.classList.add("props-row", "entry-point-row")
            container.innerHTML = `
                <span>${ep.name}</span>
                <span>${ep.is_default ? "Default": "-"}</span>
                <button ${ep.is_default ? "disabled" : ""} onclick="deleteEntryPoint(${ep.id})" class="gen-btn" >Delete</button>
                <button onclick="RUN_EP(${ep.id})" class="gen-btn" >Run</button>
            `
            epElem.appendChild(container)
        }

        epElem.innerHTML = epElem.innerHTML + `
            <button class="gen-btn new-entry-btn" onclick="newEntryPointModal.open()">&plus;</button>`
    }
}

const displaySchedule = (sched, schedElem) => {
    schedElem = schedElem || document.getElementById("schedule")
    if(schedElem) {
        schedElem.innerHTML = ""
        const headers = document.createElement("div")
        headers.classList.add("props-header", "schedule-header")
        headers.innerHTML = `
            <span>Entry Point Name</span>
            <span>Every</span>
            <span>At</span>
            <span>Timezone</span>
        `
        schedElem.appendChild(headers)

        for (const sch of sched) {
            const container = document.createElement("div")
            container.classList.add("props-row", "schedule-row")
            container.innerHTML = `
                <span>${sch.name}</span>
                <span>${sch.every}</span>
                <span>${sch.at}</span>
                <span>${sch.tzname}</span>
                <button onclick="deleteSchedule(${sch.ep_id}, ${sch.id})" class="gen-btn" >Delete</button>
            `
            schedElem.appendChild(container)
        }

        const newSchedBtn = createElementFromHTML(`<button class="gen-btn new-entry-btn">&plus;</button>`)
        newSchedBtn.onclick = () => {
            API.getEntryPoints().then(eps=>{
                newSchedModal.open().then(content=>{
                    const eps_dropdown = content.querySelector('select[name="epid"]')
                    for (const ep of eps) {
                        const opt = createElementFromHTML(`<option value="${ep.id}">${ep.name}</option>`)
                        if (ep.is_default) opt.selected = true
                        eps_dropdown.appendChild(opt)
                    }
                })
            })
        }
        schedElem.appendChild(newSchedBtn)

    }
}


const loadProjectProps = () => {
    API.getProperties().then(props=>{
        // console.log(props)
        displayEntryPoints(props.entry_points)
        displaySchedule(props.schedule)
    })
}


const addNewEntryPoint = (btn) => {
    const file = btn.parentElement.querySelector('input[name="file"]').value.trim()
    const func = btn.parentElement.querySelector('input[name="func"]').value.trim()
    const make_default = btn.parentElement.querySelector('input[name="make_default"]').checked
    API.newEntryPoint(file, func, make_default).then(res=>{
        displayEntryPoints(res)
        newEntryPointModal.close()
    }).catch(err=>AlertModal.open(err))
}


const deleteEntryPoint = (epid) => {
    ConfirmModal.open("Are you sure you want to delete this entry point?",
        ()=>{
            API.deleteEntryPoint(epid).then(()=>{
                loadProjectProps()
            }).catch(err=>AlertModal.open(err))
        }
    )
}


const addNewSchedule = (btn) => {
    const epid = btn.parentElement.querySelector('select[name="epid"]').value.trim()
    const every = btn.parentElement.querySelector('input[name="every"]').value.trim()
    const at = btn.parentElement.querySelector('input[name="at"]').value.trim()
    let tzname = btn.parentElement.querySelector('input[name="tzname"]').value.trim()
    tzname = (tzname==='') ? null : tzname
    API.newSchedule(epid, every, at, tzname).then(res=>{
        displaySchedule(res)
        newSchedModal.close()
    }).catch(err=>AlertModal.open(err))
}


const deleteSchedule = (epid, sched_id) => {
    ConfirmModal.open("Are you sure you want to delete this schedule?",
        ()=>{
            API.deleteSchedule(epid, sched_id).then(()=>{
                loadProjectProps()
            }).catch(err=>AlertModal.open(err))
        }
    )
}



const openProjectProperties = () => {
    projectPropsModal.open().then(popup=>{
        loadProjectProps()
    })
}


const projPropsSelect = (btn, tabId) => {
    btn.parentElement.parentElement.querySelectorAll('.tab').forEach(b=>b.classList.remove('selected'))
    btn.parentElement.querySelectorAll('.tab-bar-btn').forEach(b=>b.classList.remove('selected'))
    btn.classList.add('selected')
    document.getElementById(tabId).classList.add('selected')
}



const openProjectMenu = (ev) => {
    sz = ev.target.getBoundingClientRect()
    let menu = new ContextMenu(sz.x, sz.y)

    menu.addNewOption("Save (ctrl+s)", ()=>{
        SAVE()
        menu.close()
    })
    menu.addNewOption("Run (ctrl+b)", ()=>{
        RUN()
        menu.close()
    })
    menu.addNewOption("Properties", ()=>{
        openProjectProperties()
        menu.close()
    })

    menu.addNewOption("Close Project", ()=>{
        menu.close()
        window.location = "/"
    })
    menu.open()

}

// openProjectProperties()
