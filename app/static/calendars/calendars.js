function generateAvailability(startTime, date, interval, busy=null) {
    const period = 'm';
    let d = moment("23:59:59", "HH:mm:ss").diff(moment(startTime, "HH:mm:ss"), 'minutes');
    const periodsInADay = moment.duration(d, 'minutes').as(period);

    const times = [];
    const startTimeMoment = moment(startTime, 'hh:mm:ssZ');

    for (let i = 0; i <= periodsInADay; i += interval) {
        startTimeMoment.add(i === 0 ? 0 : interval, period);
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
                <div id="myc-available-time-container">` + instance.getAvailableTimes() + `</div>
            </div>
        </div>
    `;

    document.getElementById('picker').innerHTML = ret;
}