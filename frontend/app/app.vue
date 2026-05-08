<template>
  <div class="min-h-screen bg-gray-50 text-gray-900">
    <header class="bg-indigo-600 shadow-lg">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <h1 class="text-3xl font-bold text-white tracking-tight">
          Speech Recognition Portal
        </h1>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div class="bg-white rounded-xl shadow-xl p-8 border border-gray-100">
        <h2 class="text-2xl font-semibold mb-6 text-indigo-700">
          Transcription Service
        </h2>

        <div class="grid gap-8">
          <section class="space-y-4">
            <h3 class="text-lg font-semibold">1. Connexion</h3>
            <div class="grid gap-4 sm:grid-cols-2">
              <label class="block">
                <span class="text-sm font-medium text-gray-700"
                  >Nom d'utilisateur</span
                >
                <input
                  v-model="username"
                  type="text"
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
              </label>
              <label class="block">
                <span class="text-sm font-medium text-gray-700"
                  >Mot de passe</span
                >
                <input
                  v-model="password"
                  type="password"
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
              </label>
            </div>
            <button
              @click="login"
              :disabled="isLoggingIn"
              class="inline-flex items-center justify-center rounded-md bg-indigo-600 px-5 py-3 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {{ isLoggingIn ? "Connexion..." : "Se connecter" }}
            </button>
            <p v-if="token" class="text-sm text-green-700">
              Connecté avec succès. Token JWT stocké localement.
            </p>
            <p v-if="loginError" class="text-sm text-red-600">
              {{ loginError }}
            </p>
          </section>

          <section class="space-y-4">
            <h3 class="text-lg font-semibold">2. Enregistrement vocal</h3>
            <div class="grid gap-4 sm:grid-cols-2">
              <button
                @click="toggleRecording"
                :disabled="!token"
                class="rounded-md border border-indigo-600 bg-white px-5 py-3 text-sm font-medium text-indigo-700 shadow-sm hover:bg-indigo-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {{
                  isRecording
                    ? "Arrêter l’enregistrement"
                    : "Démarrer l’enregistrement"
                }}
              </button>
              <div class="rounded-md border border-gray-200 bg-gray-50 p-4">
                <p class="text-sm text-gray-700">État du microphone :</p>
                <p class="mt-1 font-semibold">
                  {{ isRecording ? "En enregistrement" : "Prêt" }}
                </p>
              </div>
            </div>
            <p class="text-sm text-gray-500">
              Le système enregistre votre voix directement depuis le navigateur
              et l’envoie au backend pour transcription.
            </p>

            <label class="block">
              <span class="text-sm font-medium text-gray-700"
                >Ou charger un fichier audio existant</span
              >
              <input
                @change="handleFileUpload"
                type="file"
                accept="audio/*"
                class="mt-2 block w-full text-sm text-gray-600 file:mr-4 file:rounded-full file:border-0 file:bg-indigo-600 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white hover:file:bg-indigo-700"
              />
            </label>

            <div v-if="audioUrl" class="space-y-2">
              <audio
                controls
                :src="audioUrl"
                class="w-full rounded-md border border-gray-200"
              ></audio>
              <p class="text-sm text-gray-600">
                Enregistrement prêt à être transcrit.
              </p>
            </div>
          </section>

          <section class="space-y-4">
            <h3 class="text-lg font-semibold">
              3. Paramètres de transcription
            </h3>
            <label class="block">
              <span class="text-sm font-medium text-gray-700">Modèle</span>
              <select
                v-model="modelType"
                class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              >
                <option value="wav2vec2">
                  facebook/wav2vec2-base-960h (Rapide)
                </option>
                <option value="whisper-tiny">
                  openai/whisper-tiny (Précis)
                </option>
              </select>
            </label>
            <button
              @click="submitTranscription"
              :disabled="!audioBlob || !token || isProcessing"
              class="inline-flex items-center justify-center rounded-md bg-indigo-600 px-5 py-3 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50"
            >
              {{ isProcessing ? "Envoi en cours..." : "Transcrire l’audio" }}
            </button>
            <p class="text-sm text-gray-500">
              Vous pouvez enregistrer, vérifier le fichier audio, puis lancer la
              transcription sécurisée.
            </p>
          </section>

          <section class="space-y-4">
            <h3 class="text-lg font-semibold">4. Résultat</h3>
            <div class="space-y-2">
              <p class="text-sm text-gray-700">
                ID de tâche :
                <span class="font-medium">{{ taskId || "Aucune tâche" }}</span>
              </p>
              <p class="text-sm text-gray-700">
                Statut :
                <span class="font-medium">{{ status || "En attente" }}</span>
              </p>
              <p v-if="transcript" class="text-sm text-gray-700">
                Texte transcrit :
              </p>
              <div
                v-if="transcript"
                class="whitespace-pre-wrap rounded-md border border-gray-200 bg-gray-50 p-4 text-sm text-gray-800"
              >
                {{ transcript }}
              </div>
              <p v-if="taskError" class="text-sm text-red-600">
                {{ taskError }}
              </p>
            </div>
          </section>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from "vue";

const username = ref("admin");
const password = ref("admin123");
const token = ref("");
const modelType = ref("wav2vec2");
const isRecording = ref(false);
const isLoggingIn = ref(false);
const isProcessing = ref(false);
const loginError = ref("");
const taskError = ref("");
const status = ref("");
const taskId = ref("");
const transcript = ref("");
const audioUrl = ref("");
const audioBlob = ref(null);
const mediaRecorder = ref(null);
const audioChunks = ref([]);

const apiBase = useRuntimeConfig().public.apiBase;

const handleFileUpload = async (event) => {
  const files = event.target.files;
  if (!files || files.length === 0) {
    return;
  }
  const file = files[0];
  audioBlob.value = file;
  audioUrl.value = URL.createObjectURL(file);
  taskError.value = "";
};

const login = async () => {
  loginError.value = "";
  isLoggingIn.value = true;
  try {
    const formData = new URLSearchParams();
    formData.append("username", username.value);
    formData.append("password", password.value);

    const response = await fetch(`${apiBase}/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData.toString(),
    });

    if (!response.ok) {
      const data = await response.json();
      loginError.value = data.detail || "Échec de la connexion";
      return;
    }

    const data = await response.json();
    token.value = data.access_token;
    window.localStorage.setItem("jwt_token", token.value);
  } catch (err) {
    loginError.value = "Erreur de connexion au serveur";
  } finally {
    isLoggingIn.value = false;
  }
};

const toggleRecording = async () => {
  if (isRecording.value) {
    stopRecording();
    return;
  }

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    taskError.value =
      "Votre navigateur ne prend pas en charge l’enregistrement audio.";
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks.value = [];
    mediaRecorder.value = new MediaRecorder(stream);

    mediaRecorder.value.addEventListener("dataavailable", (event) => {
      if (event.data && event.data.size > 0) {
        audioChunks.value.push(event.data);
      }
    });

    mediaRecorder.value.addEventListener("stop", () => {
      const blobType = audioChunks.value[0]?.type || "audio/webm";
      audioBlob.value = new Blob(audioChunks.value, { type: blobType });
      audioUrl.value = URL.createObjectURL(audioBlob.value);
    });

    mediaRecorder.value.start();
    isRecording.value = true;
    taskError.value = "";
  } catch (err) {
    taskError.value = "Impossible d’accéder au microphone.";
  }
};

const stopRecording = () => {
  if (mediaRecorder.value) {
    mediaRecorder.value.stop();
    mediaRecorder.value.stream.getTracks().forEach((track) => track.stop());
  }
  isRecording.value = false;
};

const submitTranscription = async () => {
  if (!audioBlob.value) {
    taskError.value =
      "Aucun enregistrement disponible. Veuillez enregistrer votre voix d’abord.";
    return;
  }
  if (!token.value) {
    taskError.value =
      "Connectez-vous avant de faire une demande de transcription.";
    return;
  }

  isProcessing.value = true;
  taskError.value = "";
  status.value = "Envoi du fichier...";
  transcript.value = "";
  taskId.value = "";

  try {
    const formData = new FormData();
    const filename = audioBlob.value?.name || "recording.webm";
    formData.append("file", audioBlob.value, filename);
    formData.append("model_type", modelType.value);

    const response = await fetch(`${apiBase}/transcribe`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token.value}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const data = await response.json();
      taskError.value = data.detail || "Erreur lors de l’envoi du fichier.";
      return;
    }

    const data = await response.json();
    taskId.value = data.task_id;
    status.value = "Tâche créée";
    pollTask(data.task_id);
  } catch (err) {
    taskError.value = "Impossible de contacter l’API de transcription.";
  } finally {
    isProcessing.value = false;
  }
};

const pollTask = async (id) => {
  status.value = "Traitement en cours...";
  const interval = setInterval(async () => {
    try {
      const response = await fetch(`${apiBase}/tasks/${id}`, {
        headers: { Authorization: `Bearer ${token.value}` },
      });
      if (!response.ok) {
        clearInterval(interval);
        taskError.value = "Tâche introuvable ou autorisation manquante.";
        return;
      }
      const data = await response.json();
      status.value = data.status;

      if (data.status === "COMPLETED") {
        transcript.value = data.result || "Aucune transcription retournée.";
        clearInterval(interval);
      }
      if (data.status === "FAILED") {
        taskError.value = data.error || "La transcription a échoué.";
        clearInterval(interval);
      }
    } catch (err) {
      clearInterval(interval);
      taskError.value = "Impossible de vérifier le statut de la tâche.";
    }
  }, 2500);
};

if (process.client) {
  const storedToken = window.localStorage.getItem("jwt_token");
  if (storedToken) {
    token.value = storedToken;
  }
}
</script>
