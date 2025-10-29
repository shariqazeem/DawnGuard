# core/memory_views.py - Encrypted Family Memory Views
"""
Family Memory: Digital journal system with AI-powered weekly summaries
- Daily journal entries (encrypted locally)
- AI weekly summaries
- Milestone tracking
- Searchable family history
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta, date
import json

from .models import (
    FamilyMember,
    FamilyJournalEntry,
    FamilyWeeklySummary,
    FamilyMemoryMilestone
)
from .utils.llm_handler import LLMHandler

llm_handler = LLMHandler()


@login_required
def memory_home(request):
    """
    Family Memory dashboard
    Shows: Recent entries, weekly summaries, milestones
    """
    try:
        family_member = FamilyMember.objects.get(user=request.user)

        # Get recent journal entries (own + shared)
        my_entries = FamilyJournalEntry.objects.filter(
            author=family_member
        )[:5]

        shared_entries = FamilyJournalEntry.objects.filter(
            Q(is_private=False) | Q(shared_with=family_member)
        ).exclude(author=family_member)[:5]

        # Get recent weekly summaries
        weekly_summaries = FamilyWeeklySummary.objects.all()[:4]

        # Get upcoming/recent milestones
        today = date.today()
        recent_milestones = FamilyMemoryMilestone.objects.filter(
            milestone_date__lte=today
        )[:5]

        upcoming_milestones = FamilyMemoryMilestone.objects.filter(
            milestone_date__gt=today
        )[:5]

        # Stats
        total_entries = FamilyJournalEntry.objects.filter(author=family_member).count()
        total_summaries = FamilyWeeklySummary.objects.count()
        total_milestones = FamilyMemoryMilestone.objects.count()

        # This week's entries count
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        this_week_entries = FamilyJournalEntry.objects.filter(
            entry_date__gte=week_start,
            entry_date__lte=week_end
        ).count()

        context = {
            'family_member': family_member,
            'my_entries': my_entries,
            'shared_entries': shared_entries,
            'weekly_summaries': weekly_summaries,
            'recent_milestones': recent_milestones,
            'upcoming_milestones': upcoming_milestones,
            'total_entries': total_entries,
            'total_summaries': total_summaries,
            'total_milestones': total_milestones,
            'this_week_entries': this_week_entries,
            'today': today,
        }

        return render(request, 'memory/memory_home.html', context)

    except FamilyMember.DoesNotExist:
        # Create family member if doesn't exist
        family_member = FamilyMember.objects.create(
            user=request.user,
            display_name=request.user.username.title(),
            role='admin'
        )
        return redirect('memory_home')


@login_required
@csrf_exempt
def create_journal_entry(request):
    """
    Create a new journal entry
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    try:
        family_member = FamilyMember.objects.get(user=request.user)
        data = json.loads(request.body)

        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        mood = data.get('mood', 'okay')
        entry_date_str = data.get('entry_date')
        is_private = data.get('is_private', False)
        tags = data.get('tags', [])

        if not title or not content:
            return JsonResponse({'error': 'Title and content required'}, status=400)

        # Parse entry date
        if entry_date_str:
            entry_date = datetime.strptime(entry_date_str, '%Y-%m-%d').date()
        else:
            entry_date = date.today()

        # Create journal entry
        entry = FamilyJournalEntry.objects.create(
            author=family_member,
            title=title,
            content=content,
            mood=mood,
            entry_date=entry_date,
            is_private=is_private,
            tags=tags
        )

        # AI sentiment analysis (if available)
        if llm_handler.available:
            try:
                sentiment_prompt = f"Analyze the sentiment of this journal entry on a scale from -1 (very negative) to 1 (very positive). Return only a number between -1 and 1.\n\n{content}"
                sentiment_response = llm_handler.generate_response(sentiment_prompt, max_tokens=10)
                try:
                    sentiment_score = float(sentiment_response.strip())
                    entry.sentiment_score = max(-1.0, min(1.0, sentiment_score))
                except:
                    entry.sentiment_score = 0.0

                entry.ai_processed = True
                entry.save()
            except Exception as e:
                print(f"AI sentiment analysis failed: {e}")

        return JsonResponse({
            'success': True,
            'entry_id': entry.id,
            'message': f'Journal entry "{title}" saved!',
            'mood_emoji': entry.get_mood_emoji()
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def view_journal_entries(request):
    """
    View all journal entries (paginated)
    """
    try:
        family_member = FamilyMember.objects.get(user=request.user)

        # Get filter parameters
        filter_by = request.GET.get('filter', 'all')  # all, mine, shared
        mood_filter = request.GET.get('mood')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')

        # Base query
        if filter_by == 'mine':
            entries = FamilyJournalEntry.objects.filter(author=family_member)
        elif filter_by == 'shared':
            entries = FamilyJournalEntry.objects.filter(
                Q(is_private=False) | Q(shared_with=family_member)
            ).exclude(author=family_member)
        else:  # all
            entries = FamilyJournalEntry.objects.filter(
                Q(author=family_member) |
                Q(is_private=False) |
                Q(shared_with=family_member)
            )

        # Apply filters
        if mood_filter:
            entries = entries.filter(mood=mood_filter)
        if date_from:
            entries = entries.filter(entry_date__gte=date_from)
        if date_to:
            entries = entries.filter(entry_date__lte=date_to)

        entries = entries.distinct()[:50]

        context = {
            'family_member': family_member,
            'entries': entries,
            'filter_by': filter_by,
            'mood_filter': mood_filter,
        }

        return render(request, 'memory/journal_entries.html', context)

    except FamilyMember.DoesNotExist:
        return redirect('memory_home')


@login_required
@csrf_exempt
def generate_weekly_summary(request):
    """
    Generate AI weekly summary from journal entries
    "AI, summarize our week as a family"
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    try:
        family_member = FamilyMember.objects.get(user=request.user)
        data = json.loads(request.body)

        # Get week parameters
        week_start_str = data.get('week_start')
        if week_start_str:
            week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
        else:
            # Default to current week
            today = date.today()
            week_start = today - timedelta(days=today.weekday())

        week_end = week_start + timedelta(days=6)

        # Get all entries for this week (non-private)
        week_entries = FamilyJournalEntry.objects.filter(
            entry_date__gte=week_start,
            entry_date__lte=week_end,
            is_private=False
        ).order_by('entry_date')

        if week_entries.count() == 0:
            return JsonResponse({
                'success': False,
                'error': 'No journal entries found for this week. Write some memories first!'
            }, status=400)

        # Compile all entries for AI
        entries_text = []
        authors = set()
        moods = []

        for entry in week_entries:
            authors.add(entry.author.display_name)
            moods.append(entry.mood)
            entries_text.append(
                f"{entry.author.display_name} ({entry.entry_date.strftime('%A')}): {entry.title}\n{entry.content}"
            )

        # Determine overall mood (most common)
        from collections import Counter
        mood_counts = Counter(moods)
        overall_mood = mood_counts.most_common(1)[0][0] if moods else 'happy'

        # Generate AI summary
        summary_text = ""
        highlights = []

        if llm_handler.available:
            try:
                ai_prompt = f"""You are a warm, family-oriented AI assistant creating a beautiful weekly summary for a family.

Read these journal entries from the week of {week_start.strftime('%B %d')} to {week_end.strftime('%B %d, %Y')}:

{chr(10).join(entries_text)}

Create a warm, emotional, and beautiful 2-paragraph summary of this week. Focus on:
- Happy moments and achievements
- Family bonding and activities
- Growth and milestones
- Emotional tone

Write in a warm, storytelling style that the family will treasure. Start with "This week..." """

                summary_text = llm_handler.generate_response(ai_prompt, max_tokens=300)

                # Extract highlights (ask AI)
                highlights_prompt = f"""Based on these journal entries, list 3-5 key highlights from the week as short bullet points (one line each, no dashes):

{chr(10).join(entries_text)}

Return only the highlights, one per line."""

                highlights_response = llm_handler.generate_response(highlights_prompt, max_tokens=150)
                highlights = [h.strip() for h in highlights_response.strip().split('\n') if h.strip()][:5]

            except Exception as e:
                print(f"AI summary generation failed: {e}")
                summary_text = f"This week ({week_start.strftime('%B %d')} - {week_end.strftime('%B %d')}), our family shared {week_entries.count()} memories together. " + \
                             " ".join([f"{entry.author.display_name} wrote about {entry.title.lower()}." for entry in week_entries[:3]])
                highlights = [entry.title for entry in week_entries[:5]]

        else:
            # Fallback without AI
            summary_text = f"During the week of {week_start.strftime('%B %d')} to {week_end.strftime('%B %d')}, " + \
                          f"{', '.join(authors)} shared {week_entries.count()} journal entries. " + \
                          " ".join([f"{entry.author.display_name} reflected on {entry.title.lower()}." for entry in week_entries[:3]])
            highlights = [entry.title for entry in week_entries[:5]]

        # Create weekly summary
        week_number = week_start.isocalendar()[1]
        year = week_start.year

        summary, created = FamilyWeeklySummary.objects.get_or_create(
            year=year,
            week_number=week_number,
            defaults={
                'week_start': week_start,
                'week_end': week_end,
                'ai_summary': summary_text,
                'highlights': highlights,
                'overall_mood': overall_mood,
                'total_entries': week_entries.count(),
                'participating_members': list(authors),
                'generated_by': family_member
            }
        )

        if not created:
            # Update existing
            summary.ai_summary = summary_text
            summary.highlights = highlights
            summary.overall_mood = overall_mood
            summary.total_entries = week_entries.count()
            summary.participating_members = list(authors)
            summary.save()

        # Link entries to summary
        summary.entries.set(week_entries)

        return JsonResponse({
            'success': True,
            'summary_id': summary.id,
            'summary': summary_text,
            'highlights': highlights,
            'mood': overall_mood,
            'mood_emoji': summary.get_mood_emoji(),
            'entries_count': week_entries.count(),
            'message': f'✨ Weekly summary generated for {summary.get_week_label()}!'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def view_weekly_summaries(request):
    """
    View all weekly summaries (timeline)
    """
    try:
        family_member = FamilyMember.objects.get(user=request.user)

        summaries = FamilyWeeklySummary.objects.all()[:20]

        context = {
            'family_member': family_member,
            'summaries': summaries,
        }

        return render(request, 'memory/weekly_summaries.html', context)

    except FamilyMember.DoesNotExist:
        return redirect('memory_home')


@login_required
@csrf_exempt
def search_memories(request):
    """
    AI-powered memory search
    "Show me all the happy memories from summer"
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    try:
        family_member = FamilyMember.objects.get(user=request.user)
        query = request.GET.get('q', '').strip()

        if not query:
            return JsonResponse({'results': []})

        # Search in journal entries
        entries = FamilyJournalEntry.objects.filter(
            Q(author=family_member) |
            Q(is_private=False) |
            Q(shared_with=family_member)
        ).filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(tags__icontains=query)
        ).distinct()[:20]

        results = []
        for entry in entries:
            results.append({
                'type': 'journal_entry',
                'id': entry.id,
                'title': entry.title,
                'author': entry.author.display_name,
                'date': entry.entry_date.isoformat(),
                'mood': entry.mood,
                'mood_emoji': entry.get_mood_emoji(),
                'preview': entry.content[:150] + '...' if len(entry.content) > 150 else entry.content
            })

        return JsonResponse({'results': results})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
