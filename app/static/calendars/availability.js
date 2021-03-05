let interval = 30;
let startTime = '7:00';
let day = new Date();
let myHours = generateAvailability(startTime, day, interval, null);

var instance = $('#picker').markyourcalendar({
    availability: myHours,
    isMultiple: false,
    startDate: day,
    weekdays: ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'],
    onClickNavigator:function(ev, instance) {
         instance.setAvailability(myHours);
    },
    onClick: function(ev, data) {
        document.getElementById('selected-date-confirm').classList.remove('hidden');
        document.getElementById('selected-date').innerText = FormatDate(new Date(data));
    },
});

function addDays(date, days) {
    var result = new Date(date);
    result.setDate(result.getDate() + days);
    return result;
}

function FormatDate(date){
    let dt = moment(date).format('YYYY-MM-DD hh:mm:ss Z')
    let d = moment(date).format('MMMM Do YYYY');
    let h = String((date.getHours())).length === 1 ? '0' + date.getHours() : date.getHours();
    let m = String((date.getMinutes())).length === 1 ? '0' + date.getMinutes() : date.getMinutes();
    let t = h + ':' + m;
    let tz = moment(date).format('Z');

    document.getElementById('datetime').value = dt;
    document.getElementById('date').value = d;
    document.getElementById('start-time').value = t;
    document.getElementById('tz-offset').value = tz;
    return moment(date).format('dddd, MMMM Do, YYYY @ h:mm a');
}

<!-- FlatPickr -->
$("#calendar").flatpickr({
    inline: true,
    disable: [
        function (date) {
            return (date < new Date().addDays(-1));
        }
    ],
    onChange: function(selectedDates, dateStr, instance) {
        UpdateAvailability(selectedDates);
    }
});

function UpdatePicker(selectedDate, busy=null){
    day = new Date(selectedDate);
    instance.setStartDate(day);

    if (busy !== null){
        let hours = generateAvailability(startTime, day, interval, busy)

        if (hours.length > 0)
            instance.setAvailability(hours);
    }
    render(instance);
}

<!-- Update availability -->
function UpdateAvailability(selectedDate=null){
    let checkboxes = document.getElementsByName('calendar-checkbox');

    // Update the instance
    if (selectedDate !== null){
        UpdatePicker(selectedDate);
    }

    let date = instance.getStartDate();
    let tz_offset = instance.getTZOffset();

    let checked = [];
    for (let i=0; i < checkboxes.length; i++) {
         if (checkboxes[i].checked) {
             checked.push({'id': checkboxes[i].id, 'account': checkboxes[i].dataset.account });
         }
    }

    $.ajax({
        url: "{{ url_for('user.update_availability') }}",
        type: 'POST',
        data: {'calendar_ids': JSON.stringify(checked), 'user_id': '{{ current_user.id }}', 'date': date, 'tz_offset': tz_offset},
        success: function (response) {
            if ('success' in response && response['success'] === true && 'busy' in response) {
                let busy = response['busy'];
                UpdatePicker(instance.getStartDateCurrentTime(), busy);
            }
        },
        error: function (xhr) {
        }
    });

    // Reload the page
    //Reload();
}