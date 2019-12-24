let socket = io()
let readytoconvert = true

function matchYoutubeUrl(url) {
    var p = /^(?:https?:\/\/)?(?:m\.|www\.)?(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))((\w|-){11})(?:\S+)?$/;
    if(url.match(p)){
        return url.match(p)[1];
    }
    return false;
}

$("#main_input").on("change keydown keyup", function () {
    let url = $("#main_input").val()
    let matchResult = matchYoutubeUrl(url)

    if (url === "") {
        $("main .convert-section .error").addClass("none")
        $("main .convert-section .convert").addClass("none")
        return
    }

    if (matchResult) {
        $("main .convert-section .error").addClass("none")
        $("main .convert-section .convert").removeClass("none")
    }
    else {
        $("main .convert-section .error").removeClass("none")
        $("main .convert-section .convert").addClass("none")
    }
})

$("main .convert-section .convert").click(function () {
    let url = $("#main_input").val()
    let matchResult = matchYoutubeUrl(url)

    if (matchResult && readytoconvert) {
        let data = {
            "id": matchResult
        }
        socket.emit("convertRequest", data)
        $(this).addClass("state-1")
        $(this).text("Please wait")
        readytoconvert = false
    }
})

socket.on("convert_progress", function (data) {
    if (!readytoconvert) {
        $("main .convert-section .convert").addClass("none")
        $("main .convert-section .convert").removeClass("state-1")
        $("main .convert-section .convert").text("Convert to Mp3")
        readytoconvert = true
    }

    if (data['complete']) {
        $(".progress-section").addClass("none")
    }
    else {
        $(".progress-section").removeClass("none")
        $(".progress-section .progress").css("width", `${data['percentage']}%`)
        $(".progress-section .message").text(data["process"])
    }
})

socket.on("convert_info", function (data) {
    $("#main_background").attr("src", data['thumbnail'])
})

socket.on("convert_complete", function (data) {
    $(".result").removeClass("none")
    $(".convert-section .convert").addClass("none")
    $(".convert-section .convert").text("Convert to Mp3")


    $(".result .thumbnail img").attr("src", data['thumbnail'])
    $(".result .details > h2").text(data['title'])
    $(".result .details-1 .views").text(data['views'])
    $(".result .likes").text(data['likes'])
    $(".result .dislikes").text(data['dislikes'])
    $(".result .downloads").text(data['downloads'])
    $(".result .cached").text(data['cached'])
    $(".result .download-section .last-download").text(data['last_download'])
    $(".result .download-section .uploaded").text(data['upload_date'])
    $(".result .download-section .download").attr("data-link", data['download_url'])
})
