from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.authentication import JWTAuthentication

from authentication.models import User
from core.models import UserProfile, UserInterest
from core.serializers import UserProfileSerializer
from rest_framework.authentication import get_authorization_header
from utils.common import api_error_response, api_success_response
from eon_backend.settings import SECRET_KEY
import jwt


class UserViewSet(ModelViewSet):
    authentication_classes = (JWTAuthentication,)
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    lookup_field = "user_id"

    def update(self, request, *args, **kwargs):
        token = get_authorization_header(request).split()[1]
        payload = jwt.decode(token, SECRET_KEY)
        user_id = payload['user_id']
        pk = int(kwargs.get('user_id'))
        data = request.data
        interest_list = []
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            if 'interest' in data:
                interests = data.pop('interest')
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            try:
                prev_interest = list(UserInterest.objects.filter(user=user_id).
                                     values_list('event_type', flat=True))
                interest_to_be_deleted = list(set(prev_interest).difference(interests))
                UserInterest.objects.filter(event_type_id__in=interest_to_be_deleted).update(is_active=False)
            except:
                prev_interest = []
                return api_error_response(message="Some error occur in deleting interests", status=500)

            for current in interests:
                try:
                    user_interest = UserInterest.objects.get(user=user_id, event_type_id=current, is_active=True)
                except:
                    user_interest_obj = UserInterest.objects.create(user_id=user_id, event_type_id=current).save()
                interest_list.append(current)

            response = serializer.data
            response['interest'] = interest_list
        except Exception as err:
            return api_error_response(message="Some internal error coming while updating the event", status=500)
        return api_success_response(data=response, status=200)

    def list(self, request, *args, **kwargs):
        token = get_authorization_header(request).split()[1]
        payload = jwt.decode(token, SECRET_KEY)
        user_id = payload['user_id']

        try:
            user_logged_in = user_id
            user_role = UserProfile.objects.get(user_id=user_logged_in).role.role
        except Exception as err:
            return api_error_response(message="Not able to fetch the role of the logged in user", status=500)
        data = []
        for profile in self.queryset:
            curr_profile = {'id': profile.user.id, 'name': profile.name, 'contact_number': profile.contact_number,
                            'address': profile.address, 'role': profile.role.id, 'organization': profile.organization}
            try:
                list_of_interest = list(UserInterest.objects.filter(user=profile.user.id,is_active=True).
                                        values_list('event_type', flat=True))
            except UserInterest.DoesNotExist:
                list_of_interest = []
            curr_profile['interests'] = list_of_interest

            data.append(curr_profile)

        return api_success_response(data=data, status=200)

    def retrieve(self, request, *args, **kwargs):
        token = get_authorization_header(request).split()[1]
        payload = jwt.decode(token, SECRET_KEY)
        user_logged_in = payload['user_id']
        user_id = int(kwargs.get('user_id'))

        if user_logged_in != user_id:
            return api_error_response(message="You can only view your own profile", status=400)

        profile = self.queryset.get(user_id=user_id)
        curr_profile= {'id': profile.user.id, 'name': profile.name, 'contact_number': profile.contact_number,
                       'address': profile.address, 'role': profile.role.id, 'organization': profile.organization}
        try:
            list_of_interest = list(UserInterest.objects.filter(user=user_id,is_active=True).values_list('event_type', flat=True))
        except UserInterest.DoesNotExist:
            list_of_interest = []

        curr_profile['interest'] = list_of_interest

        return api_success_response(data= curr_profile,message="user details", status=200)

