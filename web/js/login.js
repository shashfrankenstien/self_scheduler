
const LoginModal = new Modal(document.getElementById("login-box"), {
    displayStyle:'flex',
    width:'350px',
    height:'300px',
    noCloseBtn: true,
    // noTransition:true,
    containerColor: "transparent",
    noFade:true,
})
const SignupModal = new Modal(document.getElementById("signup-box"), {
    displayStyle:'flex',
    width:'350px',
    height:'450px',
    noCloseBtn: true,
    // noTransition:true,
    containerColor: "transparent",
    noFade:true,
})
LoginModal.open()

function showSignup() {
    LoginModal.close()
    SignupModal.open()
}
function showLogin() {
    SignupModal.close()
    LoginModal.open()
}


function login() {
    const login_box = document.getElementById("login-box")
    const email = login_box.querySelector("[name='email']").value.trim()
    const password = login_box.querySelector("[name='password']").value.trim()
    modFetch('/login', 'POST', {email, password}).then(data => {
        window.location = "/"
    }).catch(err=>alert(err))
}



function signup() {
    const signup_box = document.getElementById("signup-box")
    const first_name = signup_box.querySelector("[name='first_name']").value.trim()
    const last_name = signup_box.querySelector("[name='last_name']").value.trim()
    const email = signup_box.querySelector("[name='email']").value.trim()
    const password = signup_box.querySelector("[name='password']").value.trim()
    const password2 = signup_box.querySelector("[name='password2']").value.trim()

    if (password===password2) {
        modFetch('/signup', 'POST', {first_name, last_name, email, password}).then(data => {
            window.location = "/"
        }).catch(err=>alert(err))
    }
}

