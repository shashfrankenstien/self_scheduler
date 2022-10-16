
class ContextMenu {

	constructor(X, Y, clickData) {
		this.menu_options_count = 0
		this.left_position = X
		this.top_position = Y

		this.elem = document.createElement('div')
		this.elem.style.top = `${this.top_position}px`
		this.elem.style.left = `${this.left_position}px`
		this.elem.classList.add('context-menu', 'card-shadow')
		this.elem.setAttribute("tabindex", "0")

		this.clippers = []

		if (clickData) {
			this.addOption(this.createCopyOption("Copy", clickData))
		}
		this.elem.addEventListener('blur', (e)=>this._destroy())
		// this.elem.addEventListener('mouseleave', (e)=>this.close())
	}

	createOption(label, action) {
		let div = document.createElement('div')
		div.classList.add('context-option')
		div.innerHTML = label
		if (action) div.addEventListener('click', action)
		return div
	}

	createCopyOption(name, data) {
		let copy = this.createOption(name)
		copy.id = `copy-${Math.random().toString(36).substring(2, 15)}`
		copy.setAttribute("data-clipboard-text", data)
		let cb = new ClipboardJS(`#${copy.id}`)
		this.clippers.push(cb)
		return copy
	}

	addOption(opt) {
		this.elem.appendChild(opt)
		this.menu_options_count += 1
	}

	addNewOption(label, action) {
		this.addOption(this.createOption(label, action))
	}

	open() {
		if (this.menu_options_count > 0) { // only open menu if options are setup
			this.elem.style.visibility = 'hidden'
			document.body.appendChild(this.elem)

			// this section handles the menu leaking out of the current viewport before making it visible
			if (this.top_position + this.elem.offsetHeight > window.innerHeight) {
				this.elem.style.top = `${this.top_position - this.elem.offsetHeight}px`
			}
			if (this.left_position + this.elem.offsetWidth > window.innerWidth) {
				this.elem.style.left = `${this.left_position - this.elem.offsetWidth}px`
			}

			this.elem.style.visibility = "visible"
			this.elem.focus()
		}
	}

	_destroy() {
		if (this.elem) {
			this.elem.remove()
			this.elem = undefined
			this.clippers.forEach(cb=>cb.destroy())
			// console.log("Closed")
		}
	}

	close() {
		if (this.elem) {
			this.elem.blur()
		}
	}
}

