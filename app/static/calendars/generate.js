function generateAvailability(startTime, endTime, date, interval, busy=null) {
    const period = 'm';
    let d = moment("23:59:59", "HH:mm:ss").diff(moment(startTime, "HH:mm:ss"), 'minutes');
    const periodsInADay = moment.duration(d, 'minutes').as(period);

    const times = [];
    const startTimeMoment = moment(startTime, 'hh:mm:ssZ');
    const endTimeMoment = moment(endTime, 'hh:mm:ssZ');

    for (let i = 0; i <= periodsInADay; i += interval) {
        // Get the Start Time moment
        startTimeMoment.add(i === 0 ? 0 : interval, period);

        // If we've reached the end time, stop adding times
        // Commenting out isSame includes the end time (i.e. 6:00pm) in available times,
        // otherwise uncommenting excludes it
        if (/*startTimeMoment.isSame(endTimeMoment) || */startTimeMoment.isAfter(endTimeMoment))
            break;

        if (busy !== null && busy.length > 0){
            let currentDateTime = moment(date).format('YYYY-MM-DD ' + startTimeMoment.format('HH:mm:ss') + 'Z');
            let exists = busy.some(x => moment(currentDateTime).isBetween(moment(JSON.stringify(x['start'])), moment(JSON.stringify(x['end']))) ||
                            moment(currentDateTime).add(interval, period).isBetween(moment(JSON.stringify(x['start'])), moment(JSON.stringify(x['end']))) ||
                            moment(currentDateTime).isSame(moment(JSON.stringify(x['start']))));
            if (!exists)
            {
                times.push(startTimeMoment.format('hh:mm a'));
            }
        }
        else{
            times.push(startTimeMoment.format('hh:mm a'));
        }
    }
    return [times];
}

function render(instance){
    var ret = `
        <div id="myc-container">
            <div id="myc-week-container">
                <div id="myc-nav-container">` + instance.getNavControl() + `</div>
                <div id="myc-dates-container">` + instance.getDatesHeader() + `</div>
                <div id="myc-available-time-container"><div id="loader"></div>` + instance.getAvailableTimes() + `</div>
            </div>
        </div>
    `;

    document.getElementById('picker').innerHTML = ret;

    // Hide the loader when rendering
    HideLoader();
}

function ShowLoader() {
    if (document.getElementById('loader'))
        document.getElementById('loader').style.display = '';

    if (document.getElementById('myc-available-time-container'))
        document.getElementById('myc-available-time-container').style.overflowY = 'hidden';
}
function HideLoader(){
    if (document.getElementById('loader'))
        document.getElementById('loader').style.display = 'none';

    if (document.getElementById('myc-available-time-container'))
        document.getElementById('myc-available-time-container').style.overflowY = 'auto';
}