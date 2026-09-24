from .aluno import AlunoSerializer, AlunoListSerializer, AlunoRetrieveSerializer
from .categoria import CategoriaSerializer
from .convite import ConviteSerializer, CreateConviteSerializer, ConfirmConviteSerializer
from .estado import EstadoSerializer
from .estoque import EstoqueSerializer, ItemSerializer
from .equipe import EquipeSerializer, EquipeListRetrieveSerializer, EquipeCardSerializer
from .instituicao import InstituicaoSerializer, InstituicaoListRetrieveSerializer
from .professor import ProfessorSerializer, ProfessorListSerializer, ProfessorRetrieveSerializer
from .projeto import ProjetoSerializer, ProjetoListSerializer, ProjetoRetrieveSerializer, ProjetoDetailWithPostsSerializer
from .post import PostCreateSerializer, PostListRetrieveSerializer
from .user import UserRegistrationSerializer, UserSerializer