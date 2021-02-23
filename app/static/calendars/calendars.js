

function addDays(date, days) {
    var result = new Date(date);
    result.setDate(result.getDate() + days);
    return result;
}

function UpdatePicker(selectedDates){
    const myHours = [
      ['1:00', '2:00', '3:00', '4:00', '5:00']
    ];

    var picker = document.getElementById('picker');
    $(picker).markyourcalendar({
        availability: myHours,
        isMultiple: false,
        startDate: selectedDates,
        onClickNavigator:function(ev, instance) {
            instance.setAvailability(myHours);
        }
    });
}