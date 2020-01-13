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

$(".result .download-section .download").click(function () {
    let video_id = $(".result").attr('data-video-id')
    socket.emit("update_item_database", {
        "video_id": video_id
    })
    window.open(
        $(this).attr('data-link'),
        '_blank'
    )
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
    $("main .convert-section .convert").removeClass("state-1")
    readytoconvert = true

    var last_download
    let cached = "Not Cached"

    if (data['last_download'] == 0) {
        last_download = "None"
    } else {
        last_download = moment(Date(data['last_download'])).fromNow()
    }

    $(".result .cached").addClass("not")

    if (data['cached']) {
        cached = "Cached"

        $(".result .cached").removeClass("not")
    }

    $(".result").attr('data-video-id', data['video_id'])
    $(".result .thumbnail img").attr("src", data['thumbnail'])
    $(".result .details > h2").text(data['title'])
    $(".result .details-1 .views").text(data['views'] + " Views")
    $(".result .likes .amount").text(data['likes'])
    $(".result .dislikes .amount").text(data['dislikes'])
    $(".result .downloads").text(data['downloads'] + " Downloads")
    $(".result .cached").text(cached)
    $(".result .download-section .last-download").text("Last download " + last_download)
    $(".result .download-section .uploaded").text("Uploaded on " + moment(data['upload_date']).format("MMM Do YY"))
    $(".result .download-section .download").attr("data-link", data['download_url'])

})

socket.on("update_results", function (data) {
    let result_id = $(".result").attr('data-video-id')

    if (result_id == data['id']) {
        let last_download = moment(Date(data['last_download'])).fromNow()

        $(".result .downloads").text(data['downloads'] + " Downloads")
        $(".result .download-section .last-download").text("Last download " + last_download)
    }
})
