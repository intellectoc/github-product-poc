"""
    This module contains various functions for user authentication, form
    handling, database operations, and exporting data to an Excel file.

"""

import datetime
import xlwt

from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseServerError
from app.forms import MyTableForm, SignUpForm, LoginForm
from app.models import MyTable
from app.filters import FormFilter


def signup(request):
    """
    The `signup` function handles the sign up process for a user,
    including form validation and saving
    the user's information.

    :param request: The `request` parameter is an object that
    represents the HTTP request made by the
    user. It contains information about the request,
    such as the user's session, the HTTP method used
    (GET, POST, etc.), and any data submitted with the request
    :return: The function `signup` returns a rendered HTML template
    called 'sign_up.html' with the form
    and 'hide_signin' variable as context.
    """
    hide_signin = False
    # The line `if request.user.is_authenticated:` is checking if the user making the request is
    # authenticated or logged in. If the user is authenticated, it means they have provided valid
    # credentials and are logged in. In this case,
    # the code redirects the user to the 'details' page.
    # If the user is not authenticated, it means they are not logged in, and the code continues to
    # execute the rest of the function.
    if request.user.is_authenticated:
        return redirect('details')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            user = form.cleaned_data.get('username')
            messages.success(
                request, f'Hi {user}, Account Created Successfully. Use your credentials to login ')
            return redirect('signin')
    else:
        form = SignUpForm()

    return render(request, 'sign_up.html', {'form': form, 'hide_signin': hide_signin})


def signin(request):
    """
    The `signin` function handles the logic for user authentication and
    login, displaying the login form and redirecting to the details page
    if the login is successful.

    :param request: The request object represents the HTTP request
    that the user made to access the
    view. It contains information about the user,
    the requested URL, and any data that was sent with the request
    :return: a rendered HTML template called 'sign_in.html' along with
    a dictionary containing the form and a boolean variable 'hide_signin'.
    """
    hide_signin = False
    if request.user.is_authenticated:
        return redirect('details')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(
                request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('details')
            messages.info(request, ' Username or Password is Incorrect')
    else:
        form = LoginForm()

    return render(request, 'sign_in.html', {'form': form, 'hide_signin': hide_signin})


def signout(request):
    """
    The function signs out the user and redirects them to the sign-in page.

    :param request: The request object represents the current HTTP request. It contains information
    about the request, such as the user making the request,
    the HTTP method used, and any data sent with the request
    :return: a redirect to the 'signin' page.
    """
    logout(request)
    return redirect('signin')


@login_required(login_url='signin')
def details(request):
    """
    This function retrieves details from a database table
    based on the user's permissions and filters
    the results using a form filter.

    :param request: The `request` parameter is an object
    that represents the HTTP request made by the user. It contains information such as the
    user's session, the requested URL, and any data sent with
    the request
    :return: a rendered HTML template called 'details.html' with the context variables 'details' and
    'filter'.
    """
    try:
        # The line `if request.user.is_superuser:` is checking if the user making the request is a
        # superuser. A superuser is a special type of user in Django that has all permissions and
        # privileges. If the user is a superuser, it means they have administrative access and can
        # perform actions that regular users cannot. In this case, if the user is a superuser, all
        # details from the `MyTable` model are retrieved and assigned to the `details` variable.
        if request.user.is_superuser:
            all_details = MyTable.objects.all()
        else:
            # The line `details = MyTable.objects.filter(user=request.user)` is filtering the
            # `MyTable` objects based on the `user` field. It retrieves all the objects from the
            # `MyTable` model where the `user` field matches the currently logged-in user
            # (`request.user`). This ensures that only the details
            # belonging to the logged-in user are
            # retrieved and displayed.
            all_details = MyTable.objects.filter(user=request.user)
        # The line `filter = FormFilter(request.GET, queryset=details)`
        # is creating an instance of the `FormFilter` class and
        # initializing it with the `request.GET` data and the `details` queryset.
        filtered = FormFilter(request.GET, queryset=all_details)
        filtered_details = filtered.qs
        return render(request, 'details.html', {'details': details, 'filter': filtered_details})
    except Exception as error:
        return HttpResponseServerError(f"An error occurred: {str(error)}")


@login_required(login_url='signin')
def addnew(request):
    """
    The `addnew` function is a view function in Django that handles
    the submission of a form, saves the
    form data to the database, and redirects the user to a details page.

    :param request: The `request` parameter is an object that
    represents the HTTP request made by the
    client. It contains information such as the request method
    (GET, POST, etc.), headers, user session,
    and any data sent with the request
    :return: The code is returning a rendered HTML template called
    'form.html' with the form object
    passed as a context variable.
    """
    form = MyTableForm()
    if request.method == 'POST':
        try:
            form = MyTableForm(request.POST)
            if form.is_valid():
                new_entry = form.save(commit=False)
                new_entry.user = request.user
                new_entry.save()
                return redirect('details')
        except Exception as error:
            return HttpResponseServerError(f"An error occurred: {str(error)}")
    return render(request, 'form.html', {'form': form})


@login_required(login_url='signin')
def edit(request, req_id):
    """
    The `edit` function handles the editing of a record in
    the `MyTable` model, checking permissions and
    validating the form data.

    :param request: The `request` parameter is an object
    that represents the HTTP request made by the
    client. It contains information such as the user
    making the request, the method used (GET, POST,
    etc.), and any data sent with the request
    :param id: The `id` parameter is the unique identifier of
    the record that needs to be edited. It is
    used to retrieve the specific record from the `MyTable` model
    :return: The code is returning different HTTP responses
    based on certain conditions.
    """
    try:
        edit_detail = MyTable.objects.get(id=req_id)
        if not (edit_detail.user == request.user or request.user.is_superuser):
            return HttpResponseForbidden("You don't have permission to edit this record.")

        contract_type = edit_detail.contract_type
        if request.method == 'POST':
            form = MyTableForm(request.POST, instance=edit_detail)
            if form.is_valid():
                form.save()
                return redirect('details')
        else:
            form = MyTableForm(instance=edit_detail)
        return render(request, 'edit.html', {'edit_detail': edit_detail,
                                             'contract_type': contract_type,
                                             'form': form})
    except MyTable.DoesNotExist:
        return HttpResponseServerError("Record not found.")
    except Exception as error:
        return HttpResponseServerError(f"An error occurred: {str(error)}")


@login_required(login_url='signin')
def delete(request, req_id):
    """
    The function deletes a record from a table if the user
    has the necessary permissions, otherwise it
    returns an appropriate error message.

    :param request: The `request` parameter is an object
    that represents the HTTP request made by the
    client. It contains information such as the user
    making the request, the HTTP method used (e.g.,
    GET, POST), and any data sent with the request
    :param id: The `id` parameter is the unique identifier
    of the record that needs to be deleted from
    the `MyTable` model
    :return: an HTTP response. If the user has permission
    to delete the record, it will redirect them to
    the 'details' page. If the record does not exist,
    it will return an HTTP response indicating that
    the record was not found. If any other exception occurs,
    it will return an HTTP response indicating
    that an error occurred, along with the error message.
    """
    try:
        detail = MyTable.objects.get(id=req_id)
        if not (detail.user == request.user or request.user.is_superuser):
            return HttpResponseForbidden("You don't have permission to delete this record.")

        detail.delete()
        return redirect('details')
    except MyTable.DoesNotExist:
        return HttpResponseServerError("Record not found.")
    except Exception as error:
        return HttpResponseServerError(f"An error occurred: {str(error)}")


def export_excel(request):
    """
    The function exports data from a database table to an Excel file
    and allows for different columns to be included based on the user's permissions.

    :param request: The `request` parameter is an object that
    represents the HTTP request made by the client. It contains information about
    the request, such as the user making the request, the
    requested URL, and any data sent with the request
    :return: an HttpResponse object.
    """
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Data_' + \
        str(datetime.datetime.now()) + '.xls'

    wbook = xlwt.Workbook(encoding='utf-8')
    wsheet = wbook.add_sheet('Data')
    rownum = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    if request.user.is_superuser:
        columns = ['Client Name', 'Entry Date', 'Modified At',
                   'Contact Number', 'Vendor Name', 'Vendor Company',
                   'Rate', 'Currency', 'Contract Type', 'Status',
                   'Comments', 'User']

        for col_num in range(len(columns)):
            wsheet.write(rownum, col_num, columns[col_num], font_style)

        font_style = xlwt.XFStyle()

        rows = MyTable.objects.select_related('user').values_list('client_name',
                                                                  'date',
                                                                  'modified_at',
                                                                  'contact_number',
                                                                  'vendor_name',
                                                                  'vendor_company',
                                                                  'rate',
                                                                  'currency',
                                                                  'contract_type',
                                                                  'status',
                                                                  'comments',
                                                                  'user__username')

        for row in rows:
            rownum += 1

            for col_num in range(len(row)):
                wsheet.write(rownum, col_num, str(row[col_num]), font_style)

    else:
        columns = ['Client Name', 'Entry Date', 'Modified At', 'Contact Number', 'Vendor Name',
                   'Vendor Company', 'Rate', 'Currency', 'Contract Type', 'Status', 'Comments']

        for col_num in range(len(columns)):
            wsheet.write(rownum, col_num, columns[col_num], font_style)

        font_style = xlwt.XFStyle()

        rows = MyTable.objects.filter(user=request.user).values_list('client_name',
                                                                     'date',
                                                                     'modified_at',
                                                                     'contact_number',
                                                                     'vendor_name',
                                                                     'vendor_company',
                                                                     'rate',
                                                                     'currency',
                                                                     'contract_type',
                                                                     'status',
                                                                     'comments')

        for row in rows:
            rownum += 1

            for col_num in range(len(row)):
                wsheet.write(rownum, col_num, str(row[col_num]), font_style)

    wbook.save(response)

    return response
