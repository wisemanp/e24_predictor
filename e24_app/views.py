USE_GITHUB_RESULTS = False  # Set to True for production, False for team_id/session mode

from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from datetime import timedelta, datetime, time
from .models import Lap, Runner, Prediction
from .helpers import fetch_results

# Store the team ID in memory for simplicity (or use a database)
team_id = None

# Define runner colors using HUSL palette
runner_colors = {
    "Phil Wiseman": "#f6706c",
    "Steve Wills": "#f6c26c",
    "Mike McGonigle": "#b7f66c",
    "Anna Richardson": "#6cf6c2",
    "David Bittlestone": "#6c9af6",
    # Add more as needed
}

def input_team(request):
    if request.method == 'POST':
        # Store team_id and is_test in the session
        request.session['team_id'] = request.POST.get('team_id')
        is_test = request.POST.get('is_test') == 'on'  # Checkbox returns 'on' if checked
        request.session['is_test'] = is_test  # Save is_test in the session

        # Preload the database with 5 runners if no runners exist
        if Runner.objects.count() == 0:
            default_runners = ['Phil Wiseman', 'Steve Wills', 
                                   'Mike McGonigle', 'Anna Richardson', 'David Bittlestone']
            for name in default_runners:
                Runner.objects.create(name=name)

        return redirect('live_results')
    return render(request, 'e24_app/input_team.html')

def parse_leg_time(timestr):
    try:
        h, m, s = map(int, str(timestr).split(":"))
        return timedelta(hours=h, minutes=m, seconds=s)
    except:
        return timedelta(0)

def live_results_chatting_shit(request):
    runners = list(Runner.objects.all().order_by('name'))
    laps = list(Lap.objects.order_by('number'))

    fixed_laps = [lap for lap in laps if lap.fixed]
    predicted_laps = [lap for lap in laps if not lap.fixed]

    cumulative = timedelta()
    for lap in fixed_laps:
        if lap.laptime:
            cumulative += lap.laptime

    context = {
        'runners': runners,
        'laps': fixed_laps + predicted_laps,
        'fixed_laps': len(fixed_laps),
        'cumulative_time': str(cumulative),
    }

    return render(request, 'e24_app/live_results.html', context)

def format_timedelta(td):
    """Convert a timedelta object to a string in HH:MM:SS format."""
    if td is None:
        return ''
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def live_results(request):
    if USE_GITHUB_RESULTS:
        # Always use GitHub CSV, ignore team_id/session
        results = fetch_results(team_id=None, test=True)
        is_test=False
    else:
        # Retrieve team_id and is_test from the session
        team_id = request.session.get('team_id')
        is_test = request.session.get('is_test', False)
        results = fetch_results(team_id, test=is_test)

    # If results is empty, skip DB update and render empty table
    if not results:
        print("No results found, rendering empty results table.")
        return render(request, 'e24_app/live_results.html', {
            'laps': [],
            'runners': Runner.objects.all(),
            'total_laps': 0,
            'cumulative_time': "00:00:00",
            'range_1_to_5': range(1, 6),
        })

    # Base start time for the race (e.g., 12:00:00)
    base_time_of_day = datetime.combine(datetime.today(), time(12, 0, 0))  # Start at 12:00:00
    cumulative_time = timedelta(0)  # Start cumulative time at 0
    now = datetime.now()+timedelta(hours=1)  # Current time of day account for DST
    print('test?', is_test)
    print(f"Current time: {now}, Base time of day: {base_time_of_day}")

    # Update the database with the fetched results
    for result in results:
        # Get or create the runner
        runner, _ = Runner.objects.get_or_create(name=result['Runner'])

        # Parse the lap time
        lap_time = parse_leg_time(result['Leg Time'])  # Convert string to timedelta
        if not lap_time:
            print(f"Skipping invalid lap time for result: {result}")
            continue  # Skip invalid lap times

        # Calculate the lap's finish time
        lap_finish_time = base_time_of_day + cumulative_time + lap_time
        print(f"Lap Finish Time: {lap_finish_time}, Current Time: {now}")
        print(f"Lap Time: {lap_time}, Cumulative Time Before Update: {cumulative_time}")

        # Check if the current time is before noon
        if now.time() < time(12, 0, 0):
            
            # Allow all laps with finish times after 12:00:00
            if lap_finish_time.time() >= time(12, 0, 0):
                print(f"Allowing lap with finish time {lap_finish_time} because current time is morning")
            elif lap_finish_time.time()<= (now+timedelta(hours=1)).time():
                print(f"Allowing lap with finish time {lap_finish_time} because current time is morning")

            else:
                print(f"Skipping lap with finish time {lap_finish_time} because it is before 12:00:00")
                continue
        else:
            # Regular check for laps with finish times before the current time
            if lap_finish_time > now:
                print(f"Skipping lap with finish time {lap_finish_time} because it is after current time {now}")
                continue

        # Get or create the lap
        lap, created = Lap.objects.get_or_create(number=result['Lap'])

        # Mark laps fetched from the results website as fixed
        lap.runner = runner
        lap.laptime = lap_time
        lap.start_time = base_time_of_day + cumulative_time  # Set lap start time
        cumulative_time += lap_time  # Increment cumulative time
        lap.total_time = cumulative_time  # Set cumulative duration
        lap.fixed = True  # Mark as fixed since it's fetched from the official results
        lap.pace = format_timedelta(timedelta(seconds=lap.laptime.total_seconds() / 8)) if lap.laptime else None
        lap.save()
        print(f"Updated Cumulative Time: {cumulative_time}")

    # Query the database for laps and runners
    laps = Lap.objects.all().order_by('number')
    runners = Runner.objects.all()
    
    # Prepare data for the template
    lap_data = []
    for lap in laps:
        lap_data.append({
            'number': lap.number,
            'start_time': lap.start_time.strftime('%H:%M:%S') if lap.start_time else '',
            'runner': lap.runner.name if lap.runner else '',
            'laptime': format_timedelta(lap.laptime) if lap.laptime else '',
            'pace': lap.pace if lap.pace else '-',
            'total_time': format_timedelta(lap.total_time) if lap.total_time else '',
            'fixed': lap.fixed,
        })

    runner_data = [{'name': runner.name} for runner in runners]
    print("returning live results with laps:", lap_data)

    # Pass the cumulative time after fixed laps to the template
    return render(request, 'e24_app/live_results.html', {
        'laps': lap_data,
        'runners': runner_data,
        'total_laps': laps.count(),
        'cumulative_time': format_timedelta(cumulative_time),  # Pass cumulative time
        'range_1_to_5': range(1, 6),  # Add this to the context
        'runner_colors': runner_colors,  # Pass runner colors to the template
    })

@csrf_exempt
def save_human_inputs(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        for lap_data in data.get('laps', []):
            lap = Lap.objects.get(number=lap_data['number'])
            if not lap.fixed:  # Only update non-fixed laps
                lap.runner = Runner.objects.get_or_create(name=lap_data['runner'])[0]
                lap.laptime = lap_data['laptime']
                lap.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@csrf_exempt
def save_predictions(request):
    if request.method == "POST":
        Prediction.objects.all().update(current=False)
        import json
        data = json.loads(request.body)
        for pred in data.get('predictions', []):
            Prediction.objects.create(
                runner=pred['runner'],
                laptime=pred.get('laptime', ''),
                fixed=pred.get('fixed', False),
                current=True
            )
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)

def load_predictions(request):
    preds = Prediction.objects.filter(current=True)
    data = [
        {
            'runner': p.runner,
            'laptime': p.laptime,
            'fixed': p.fixed,
        }
        for p in preds
    ]
    return JsonResponse({'predictions': data})


