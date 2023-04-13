from rest_framework.views import APIView, Request, Response, status
from rest_framework.pagination import PageNumberPagination
from .models import Pet
from .serializers import PetSerializer
from groups.models import Group
from traits.models import Trait
from django.shortcuts import get_object_or_404


class PetsView(APIView, PageNumberPagination):
    def get(self, request: Request) -> Response:
        trait = request.query_params.get("trait", None)

        if trait is None:
            pets = Pet.objects.all()
        else:
            pets = Pet.objects.filter(traits__name__iexact=trait)

        result_page = self.paginate_queryset(pets, request)

        serializer = PetSerializer(result_page, many=True)

        return self.get_paginated_response(serializer.data)

    def post(self, request: Request) -> Response:
        serializer = PetSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        group_data = serializer.validated_data.pop("group")
        traits_data = serializer.validated_data.pop("traits")

        group = Group.objects.filter(
            scientific_name=group_data["scientific_name"]
        ).first()

        if not group:
            group = Group.objects.create(**group_data)

        pet_data = Pet.objects.create(**serializer.validated_data, group=group)

        for trait_data in traits_data:
            trait = Trait.objects.filter(name__iexact=trait_data["name"]).first()

            if not trait:
                trait = Trait.objects.create(**trait_data)

            pet_data.traits.add(trait)

        serializer = PetSerializer(pet_data)

        return Response(serializer.data, status.HTTP_201_CREATED)


class PetsDetailView(APIView):
    def get(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)

        serializer = PetSerializer(pet)

        return Response(serializer.data, status.HTTP_200_OK)

    def patch(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)

        serializer = PetSerializer(data=request.data, partial=True)

        serializer.is_valid(raise_exception=True)

        group_data = serializer.validated_data.pop("group", None)
        traits_data = serializer.validated_data.pop("traits", None)

        if group_data is not None:
            group = Group.objects.filter(
                scientific_name=group_data["scientific_name"]
            ).first()

            if not group:
                group = Group.objects.create(**group_data)

            pet.group = group

        if traits_data is not None:
            traits = []

            for trait_data in traits_data:
                trait = Trait.objects.filter(name__iexact=trait_data["name"]).first()

                if not trait:
                    trait = Trait.objects.create(**trait_data)

                traits.append(trait)

            pet.traits.set(traits)

        for key, value in serializer.validated_data.items():
            setattr(pet, key, value)

        pet.save()

        serializer = PetSerializer(pet)

        return Response(serializer.data, status.HTTP_200_OK)

    def delete(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)

        pet.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
