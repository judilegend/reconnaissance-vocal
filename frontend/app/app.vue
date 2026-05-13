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
            <h3 class="text-lg font-semibold">
              2. Enregistrement vocal (max 15s)
            </h3>
            <div class="grid gap-4 sm:grid-cols-2">
              <button
                @click="toggleRecording"
                class="rounded-md border border-indigo-600 bg-white px-5 py-3 text-sm font-medium text-indigo-700 shadow-sm hover:bg-indigo-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <!-- :disabled="!token.value || token.value === ''" -->
                {{
                  isRecording
                    ? "Arrêter l’enregistrement"
                    : "Démarrer l’enregistrement (15s max) "
                }}
              </button>
              <div class="rounded-md border border-gray-200 bg-gray-50 p-4">
                <p class="text-sm text-gray-700">État du microphone :</p>
                <p class="mt-1 font-semibold">
                  {{
                    isRecording
                      ? `En enregistrement (${recordingTime}s)`
                      : "Prêt"
                  }}
                </p>
              </div>
            </div>
            <p class="text-sm text-gray-500">
              Enregistrez votre voix pendant max 15 secondes. L'enregistrement
              s'arrête automatiquement.
            </p>

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
            <h3 class="text-lg font-semibold">3. Transcription (Wav2Vec2)</h3>
            <button
              @click="submitTranscription"
              :disabled="!audioBlob || !token || isProcessing"
              class="inline-flex items-center justify-center rounded-md bg-indigo-600 px-5 py-3 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50"
            >
              {{
                isProcessing
                  ? "Transcription en cours..."
                  : "Transcrire l’audio"
              }}
            </button>
            <p class="text-sm text-gray-500">
              La transcription utilise Wav2Vec2 avec prétraitement audio.
            </p>
          </section>

          <section class="space-y-4">
            <h3 class="text-lg font-semibold">4. Résultat (Streaming)</h3>
            <div class="space-y-2">
              <p class="text-sm text-gray-700">
                ID de tâche :
                <span class="font-medium">{{ taskId || "Aucune tâche" }}</span>
              </p>
              <p class="text-sm text-gray-700">
                Statut :
                <span class="font-medium">{{ status || "En attente" }}</span>
              </p>
              <p class="text-sm text-gray-700">Texte transcrit (streaming) :</p>
              <div
                class="whitespace-pre-wrap rounded-md border border-gray-200 bg-gray-50 p-4 text-sm text-gray-800 min-h-[100px]"
              >
                {{ streamingText }}
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
import { ref, onMounted } from "vue";

const username = ref("admin");
const password = ref("admin123");
const token = ref("");
const isRecording = ref(false);
const isLoggingIn = ref(false);
const isProcessing = ref(false);
const loginError = ref("");
const taskError = ref("");
const status = ref("");
const taskId = ref("");
const streamingText = ref("");
const audioUrl = ref("");
const audioBlob = ref(null);
const mediaRecorder = ref(null);
const audioChunks = ref([]);
const recordingTime = ref(0);
const recordingInterval = ref(null);

const apiBase = useRuntimeConfig().public.apiBase;

onMounted(() => {
  const storedToken = window.localStorage.getItem("jwt_token");
  if (storedToken) {
    token.value = storedToken;
    console.log(
      "Token JWT récupéré du localStorage:",
      token.value.substring(0, 20) + "...",
    );
  }
});

const login = async () => {
  console.log("Tentative de connexion avec username:", username.value);
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
      console.error("Erreur de connexion:", loginError.value);
      return;
    }

    const data = await response.json();
    token.value = data.access_token;
    window.localStorage.setItem("jwt_token", token.value);
    console.log(
      "Connexion réussie, token stocké:",
      token.value.substring(0, 20) + "...",
    );
  } catch (err) {
    loginError.value = "Erreur de connexion au serveur";
    console.error("Erreur réseau:", err);
  } finally {
    isLoggingIn.value = false;
  }
};

const toggleRecording = async () => {
  if (isRecording.value) {
    stopRecording();
    return;
  }

  console.log("Démarrage de l'enregistrement");
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    taskError.value =
      "Votre navigateur ne prend pas en charge l'enregistrement audio.";
    console.error("MediaDevices non supporté");
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks.value = [];
    mediaRecorder.value = new MediaRecorder(stream);

    mediaRecorder.value.addEventListener("dataavailable", (event) => {
      if (event.data && event.data.size > 0) {
        audioChunks.value.push(event.data);
        console.log("Chunk audio ajouté, taille:", event.data.size);
      }
    });

    mediaRecorder.value.addEventListener("stop", () => {
      const blobType = audioChunks.value[0]?.type || "audio/webm";
      audioBlob.value = new Blob(audioChunks.value, { type: blobType });
      audioUrl.value = URL.createObjectURL(audioBlob.value);
      console.log(
        "Enregistrement terminé, blob créé, taille:",
        audioBlob.value.size,
      );
      mediaRecorder.value.stream.getTracks().forEach((track) => track.stop());
    });

    mediaRecorder.value.start();
    isRecording.value = true;
    recordingTime.value = 0;
    taskError.value = "";

    // Auto-stop after 15 seconds
    recordingInterval.value = setInterval(() => {
      recordingTime.value++;
      if (recordingTime.value >= 15) {
        stopRecording();
      }
    }, 1000);

    console.log("Enregistrement démarré");
  } catch (err) {
    taskError.value = "Impossible d'accéder au microphone.";
    console.error("Erreur d'accès au microphone:", err);
  }
};

const stopRecording = () => {
  console.log("Arrêt de l'enregistrement");
  if (mediaRecorder.value) {
    mediaRecorder.value.stop();
  }
  if (recordingInterval.value) {
    clearInterval(recordingInterval.value);
  }
  isRecording.value = false;
  recordingTime.value = 0;
};

const submitTranscription = async () => {
  if (!audioBlob.value) {
    taskError.value =
      "Aucun enregistrement disponible. Veuillez enregistrer votre voix d'abord.";
    console.error("Aucun blob audio disponible");
    return;
  }
  if (!token.value) {
    taskError.value =
      "Connectez-vous avant de faire une demande de transcription.";
    console.error("Aucun token JWT disponible");
    return;
  }

  console.log(
    "Soumission de la transcription, taille du blob:",
    audioBlob.value.size,
  );
  isProcessing.value = true;
  taskError.value = "";
  status.value = "Envoi du fichier...";
  streamingText.value = "";
  taskId.value = "";

  try {
    const formData = new FormData();
    formData.append("file", audioBlob.value, "recording.webm");
    formData.append("model_type", "wav2vec2");

    const response = await fetch(`${apiBase}/transcribe`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token.value}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const data = await response.json();
      taskError.value = data.detail || "Erreur lors de l'envoi du fichier.";
      console.error("Erreur lors de l'envoi:", taskError.value);
      return;
    }

    const data = await response.json();
    taskId.value = data.task_id;
    status.value = "Tâche créée";
    console.log("Tâche créée:", taskId.value);
    pollTask(data.task_id);
  } catch (err) {
    taskError.value = "Impossible de contacter l'API de transcription.";
    console.error("Erreur réseau:", err);
  } finally {
    isProcessing.value = false;
  }
};

const pollTask = async (id) => {
  console.log("Début du polling pour la tâche:", id);
  status.value = "Traitement en cours...";
  const interval = setInterval(async () => {
    try {
      const response = await fetch(`${apiBase}/tasks/${id}`, {
        headers: { Authorization: `Bearer ${token.value}` },
      });
      if (!response.ok) {
        clearInterval(interval);
        taskError.value = "Tâche introuvable ou autorisation manquante.";
        console.error("Erreur lors du polling:", taskError.value);
        return;
      }
      const data = await response.json();
      status.value = data.status;
      console.log("Statut de la tâche:", data.status);

      if (data.streaming_tokens && data.streaming_tokens.length > 0) {
        streamingText.value = data.streaming_tokens
          .join("")
          .replace(/\|/g, " ");
        console.log("Tokens streaming mis à jour:", streamingText.value);
      }

      if (data.status === "COMPLETED") {
        streamingText.value = data.result || "Aucune transcription retournée.";
        clearInterval(interval);
        console.log("Transcription terminée:", streamingText.value);
      }
      if (data.status === "FAILED") {
        taskError.value = data.error || "La transcription a échoué.";
        clearInterval(interval);
        console.error("Transcription échouée:", taskError.value);
      }
    } catch (err) {
      clearInterval(interval);
      taskError.value = "Impossible de vérifier le statut de la tâche.";
      console.error("Erreur lors du polling:", err);
    }
  }, 1000);
};
</script>
